from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig # Assuming this is from your project
import asyncio
from dotenv import load_dotenv
import os
import argparse
import logging
import sys
from typing import Dict, Optional, List, Union
from enum import Enum
import time
import inspect # For checking if a function is a coroutine

# Load environment variables from .env file
load_dotenv()

# Disable anonymized telemetry for browser_use if it respects this
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("browser_agent.log"),
        logging.StreamHandler(sys.stdout) # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Browser type enum
class BrowserType(str, Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    ZEN = "zen" # Assuming Zen is a Chromium-based browser

# Progress reporter class
class ProgressReporter:
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0 # This might not be updated if agent doesn't callback
        self.start_time = time.time()
    
    def update(self, step: int = 1, message: str = ""):
        # This method is kept for potential future use or if the Agent API changes.
        # Currently, the browser_use.Agent doesn't seem to use this callback.
        self.current_step += step
        # logger.info(f"ProgressReporter updated: Step {self.current_step}, {message}") # Optional: for debugging reporter
        return None 
    
    def task_started(self):
        """Logs the beginning of the task from the reporter's perspective."""
        logger.info(f"Task started by ProgressReporter. Total steps planned: {self.total_steps}")
        print(f"Task started by ProgressReporter. Total steps planned: {self.total_steps}")
        self.start_time = time.time() # Reset start time

    def task_completed(self, actual_steps: Optional[int] = None):
        """Logs the completion of the task from the reporter's perspective."""
        # The agent logs its own steps. This reporter primarily tracks overall time.
        final_steps_reported = actual_steps if actual_steps is not None else self.current_step
        # If no steps were ever updated via `update()`, use total_steps for the message.
        if self.current_step == 0 and actual_steps is None:
             final_steps_reported = self.total_steps 
        
        elapsed = time.time() - self.start_time
        logger.info(f"Task finished according to ProgressReporter in {elapsed:.2f} seconds. Steps considered by reporter: {final_steps_reported}/{self.total_steps}.")
        print(f"Task finished according to ProgressReporter in {elapsed:.2f} seconds. Steps considered by reporter: {final_steps_reported}/{self.total_steps}.")

# Environment validation function
def validate_environment() -> bool:
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_message)
        print(f"Error: {error_message}", file=sys.stderr)
        return False
    return True

# Browser factory function
def create_browser(browser_type: BrowserType, browser_path_hint: Optional[str] = None) -> Browser:
    """
    Creates a browser instance.
    The browser_path_hint might be used by BrowserConfig if it supports launching
    a specific executable, otherwise Playwright typically uses its own managed browsers.
    """
    path_for_log = browser_path_hint # For logging purposes
    try:
        if browser_type == BrowserType.CHROME:
            # Default path is just a hint; Playwright likely uses its own Chromium.
            default_path_hint = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            path_for_log = browser_path_hint or default_path_hint
            return Browser(config=BrowserConfig(chrome_instance_path=browser_path_hint))
        elif browser_type == BrowserType.FIREFOX:
            default_path_hint = r'C:\Program Files\Mozilla Firefox\firefox.exe'
            path_for_log = browser_path_hint or default_path_hint
            return Browser(config=BrowserConfig(firefox_instance_path=browser_path_hint))
        elif browser_type == BrowserType.EDGE:
            default_path_hint = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
            path_for_log = browser_path_hint or default_path_hint
            return Browser(config=BrowserConfig(edge_instance_path=browser_path_hint))
        elif browser_type == BrowserType.ZEN:
            default_path_hint = r'C:\Program Files\Zen Browser\zen.exe' # Highly specific
            path_for_log = browser_path_hint or default_path_hint
            logger.info(f"Using Zen browser (assumed Chromium-based) with path hint: {path_for_log}")
            # Assuming Zen is Chromium-based and compatible with chrome_instance_path for Playwright
            return Browser(config=BrowserConfig(chrome_instance_path=browser_path_hint))
        else:
            # This case should ideally not be reached if argparse choices are respected
            raise ValueError(f"Unsupported browser type: {browser_type}")
    except FileNotFoundError : # This error is less likely if Playwright uses its own browsers
        logger.error(f"Browser executable hint was provided but not found for {browser_type} at path '{path_for_log}'. "
                     "However, Playwright-based libraries usually manage their own browser binaries. "
                     "Ensure Playwright browsers are installed (`python -m playwright install`).")
        raise
    except Exception as e:
        logger.error(f"Failed to create browser instance for {browser_type} (path hint: {path_for_log}): {str(e)}."
                     " Ensure Playwright browsers are installed (`python -m playwright install`).", exc_info=True)
        raise

# Task definitions
PREDEFINED_TASKS = {
    "whatsapp_summary": "Navigate to WhatsApp Web (https://web.whatsapp.com/) and locate the chat named '{chat_name}'. Scroll through the past messages in the conversation to understand the context. Summarize the key discussion points from the last {message_count} messages. Based on the conversation history, craft a relevant response that contributes meaningfully to the discussion. Send the reply in the chat. Maximum steps: {max_steps}.",
    "web_search": "Navigate to Google.com, search for '{query}', and summarize the top {result_count} results. Maximum steps: {max_steps}.",
    "email_check": "Navigate to Gmail, check for new emails in the inbox, and summarize the {email_count} most recent unread messages. Maximum steps: {max_steps}."
}

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Browser automation agent powered by LLM")
    parser.add_argument("--task", type=str, choices=list(PREDEFINED_TASKS.keys()), help="Predefined task to run")
    parser.add_argument("--custom-task", type=str, help="Custom task description if not using a predefined one")
    parser.add_argument("--browser", type=str, choices=[b.value for b in BrowserType], default=BrowserType.CHROME.value, help="Browser to use (default: chrome)")
    parser.add_argument("--browser-path", type=str, help="Optional: Path to browser executable (may be used as a hint or for non-Playwright managed browsers)")
    parser.add_argument("--timeout", type=int, default=300, help="Global timeout for the entire task in seconds (default: 300s)")
    parser.add_argument("--operation-timeout", type=int, default=60, help="Timeout for individual LLM operations in seconds (default: 60s)")
    parser.add_argument("--max-steps", type=int, default=80, help="Maximum number of steps the agent can take (default: 80)")
    
    # Task-specific arguments
    parser.add_argument("--chat-name", type=str, default=None, help="Chat name for WhatsApp task (required if --task=whatsapp_summary)")
    parser.add_argument("--message-count", type=int, default=40, help="Number of messages to analyze for WhatsApp task (default: 40)")
    parser.add_argument("--query", type=str, default=None, help="Search query for web search task (required if --task=web_search)")
    parser.add_argument("--result-count", type=int, default=5, help="Number of results to analyze for web search task (default: 5)")
    parser.add_argument("--email-count", type=int, default=5, help="Number of emails to analyze for email check task (default: 5)")
    
    parser.add_argument("--verbose", action="store_true", help="Enable verbose (DEBUG level) logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled.")
    
    # Validate environment variables
    if not validate_environment():
        return 1
    
    # Validate task-specific required arguments
    if args.task == "whatsapp_summary" and not args.chat_name:
        error_msg = "Error: --chat-name is required for the 'whatsapp_summary' task."
        logger.error(error_msg); print(error_msg, file=sys.stderr); parser.print_help(); return 1
        
    if args.task == "web_search" and not args.query:
        error_msg = "Error: --query is required for the 'web_search' task."
        logger.error(error_msg); print(error_msg, file=sys.stderr); parser.print_help(); return 1

    if not args.task and not args.custom_task:
        error_msg = "Error: No task specified. Use --task <predefined_task_name> or --custom-task \"<your_task_description>\"."
        logger.error(error_msg); print(error_msg, file=sys.stderr); parser.print_help(); return 1
    
    if args.task and args.custom_task:
        logger.warning("Both --task and --custom-task provided. Using --custom-task.")

    progress: Optional[ProgressReporter] = None
    browser: Optional[Browser] = None # Define browser here for the finally block
    try:
        if args.max_steps <= 0:
            logger.warning(f"max_steps ({args.max_steps}) must be positive. Setting to a default of 1.")
            args.max_steps = 1
        progress = ProgressReporter(args.max_steps)
        
        llm_model_name = "gemini-1.5-flash-latest" 
        logger.info(f"Initializing LLM with model: {llm_model_name}")
        llm = ChatGoogleGenerativeAI(
            model=llm_model_name,
            temperature=0, 
            timeout=args.operation_timeout,
            max_retries=2,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        browser_type_enum = BrowserType(args.browser)
        logger.info(f"Creating browser instance (hint: {browser_type_enum.value}). "
                    "Crucial: Ensure Playwright browsers are installed (`python -m playwright install`).")
        browser = create_browser(browser_type_enum, args.browser_path)
        
        # Determine task description
        task_description = ""
        if args.custom_task:
            task_description = args.custom_task
        elif args.task:
            task_params = {
                "chat_name": args.chat_name if args.chat_name is not None else "", 
                "message_count": args.message_count,
                "max_steps": args.max_steps, # Agent will use this from its task string
                "query": args.query if args.query is not None else "",
                "result_count": args.result_count,
                "email_count": args.email_count
            }
            task_description = PREDEFINED_TASKS[args.task].format(**task_params)
        
        logger.info("Initializing agent...")
        agent = Agent(
            task=task_description,
            llm=llm,
            browser=browser
        )
        
        logger.info(f"Starting task via agent (max_steps in task desc: {args.max_steps}, global timeout: {args.timeout}s): {task_description[:150]}...")
        if progress:
            progress.task_started()

        result = None
        agent_run_successful = False

        try:
            # Agent.run's max_steps might be controlled by the task string or its own defaults.
            # Passing max_steps here if the API supports it, otherwise it's in the task string.
            agent_result_object = await asyncio.wait_for(
                agent.run(max_steps=args.max_steps), # Assuming agent.run takes max_steps
                timeout=float(args.timeout)
            )
            result = agent_result_object 
            agent_run_successful = True 
            logger.info(f"Agent.run completed. Result type: {type(result)}")
            if hasattr(result, 'all_results') and isinstance(getattr(result, 'all_results'), list): 
                 logger.info(f"Agent history contains {len(result.all_results)} results.")

        except asyncio.TimeoutError:
            error_msg = f"Task timed out after {args.timeout} seconds during agent.run."
            logger.error(error_msg)
            print(f"\nError: {error_msg}", file=sys.stderr)
            return 1 
        except NotImplementedError as nie: # Specifically for Playwright/asyncio issues
            logger.error(f"NotImplementedError during agent execution: {str(nie)}", exc_info=True)
            logger.error("This often means Playwright browsers are not installed OR there's an asyncio event loop issue on Windows. "
                         "1. Ensure Playwright browsers are installed: `python -m playwright install` in your venv. "
                         "2. This script uses Python's default event loop for Windows (recommended for Python 3.8+).")
            print(f"\nError: {str(nie)}. Ensure Playwright browsers are installed (`python -m playwright install`) and try again.", file=sys.stderr)
            return 1
        except Exception as e: # Catch other errors from agent.run()
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            print(f"\nError during agent execution: {str(e)}", file=sys.stderr)
            return 1 
        
        # Visualize results if task completed successfully
        if agent_run_successful and result is not None:
            print("\n" + "=" * 50)
            print("TASK RESULTS")
            print("=" * 50)
            print(f"Task: {task_description[:100]}...")
            print(f"Browser: {browser_type_enum.value}")
            if progress: # progress reporter gives overall timing
                 print(f"Time elapsed (ProgressReporter): {time.time() - progress.start_time:.2f} seconds")
            print("\nOutput from agent:")
            print(result) 
            print("=" * 50)
            
        return 0

    except FileNotFoundError as e: 
        logger.error(f"Setup error (FileNotFound): {str(e)}")
        print(f"Setup Error: {str(e)}\nPlease ensure any specified browser path is correct, or that Playwright browsers are installed.", file=sys.stderr)
        return 1
    except ValueError as e: 
        logger.error(f"Configuration error (ValueError): {str(e)}", exc_info=True)
        print(f"Configuration Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e: # Catch errors from main setup (before agent.run more detailed try-block)
        logger.error(f"An unexpected error occurred in main setup: {str(e)}", exc_info=True)
        print(f"An unexpected error occurred in main setup: {str(e)}", file=sys.stderr)
        return 1
    finally:
        if progress: 
            progress.task_completed() 

        if browser:
            logger.info("Attempting to close browser in main finally block...")
            try:
                if hasattr(browser, 'close') and callable(browser.close):
                    # The RuntimeWarning previously indicated browser.close is a coroutine
                    if inspect.iscoroutinefunction(browser.close):
                        logger.info("Awaiting async browser.close()...")
                        await browser.close()
                    else:
                        # If not a coroutine, call directly (though Playwright's is often async)
                        logger.info("Calling sync browser.close()...")
                        browser.close() 
                elif hasattr(browser, 'quit') and callable(browser.quit): # Fallback for Selenium-like
                    logger.info("Calling browser.quit()...")
                    browser.quit()
            except Exception as e_close:
                logger.warning(f"Error during browser close/quit: {e_close}", exc_info=True)
        
if __name__ == "__main__":
    # For Python 3.8+ on Windows, the default ProactorEventLoop is generally preferred
    # and supports subprocesses better than SelectorEventLoop.
    # By REMOVING the explicit set_event_loop_policy, we allow Python (e.g. 3.12) to use its default.
    # ---
    # if sys.platform == "win32":
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # THIS LINE IS INTENTIONALLY KEPT COMMENTED OUT / REMOVED
    # ---

    exit_code = 1 # Default to error
    try:
        logger.info("Reminder: Ensure Playwright browsers are installed by running `python -m playwright install` "
                    "in your virtual environment if you encounter browser launch issues.")
        print("Reminder: Ensure Playwright browsers are installed by running `python -m playwright install` "
              "in your virtual environment if you encounter browser launch issues.", file=sys.stderr)
        
        exit_code = asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Process interrupted by user (Ctrl+C). Exiting.")
        print("\nProcess interrupted. Exiting...", file=sys.stderr)
    except Exception as e: # Catch any remaining unhandled exceptions from asyncio.run(main()) itself
        logger.critical(f"Critical error launching or during main execution: {e}", exc_info=True)
        print(f"Critical error: {e}", file=sys.stderr)
    finally:
        logging.shutdown() # Flushes and closes all logging handlers
        sys.exit(exit_code)