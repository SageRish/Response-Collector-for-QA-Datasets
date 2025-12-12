import asyncio
import time
import traceback
from typing import List, Dict, Any, Tuple
from .provider import ModelConfig
from .dataset_loader import DatasetLoader
from .client_factory import make_client
from .logger import Logger
from .progress import ProgressState
from .utils import AsyncRateLimiter

async def collect_responses(
    model_cfg: ModelConfig,
    dataset_loader: DatasetLoader,
    short_max_tokens: int,
    long_max_tokens: int,
    system_prompt: str,
    logger: Logger,
    progress_callback,
    should_stop: Any = None
) -> Tuple[List[List[Dict]], List[Dict]]:
    """
    Collects responses for a single model.
    Returns (collected_data, missing_responses).
    """
    
    client = make_client(model_cfg)
    rate_limiter = AsyncRateLimiter(max_calls=6, period=1.0)
    
    # Initialize output structure
    collected_data = dataset_loader.get_empty_structure()
    missing_responses = []
    
    # Initialize progress
    total_questions = dataset_loader.num_questions
    progress = ProgressState(
        model_alias=model_cfg.alias,
        completed=0,
        total=total_questions,
        start_time=time.time(),
        status="Running"
    )
    progress_callback(progress)
    
    logger.log(f"[{model_cfg.alias}] Starting collection...")

    async def get_response(prompt: str, max_tokens: int) -> str:
        await rate_limiter.acquire()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await client.chat.completions.create(
                model=model_cfg.model_name,
                messages=messages,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e

    try:
        for doc_idx, q_idx, entry in dataset_loader.iter_questions():
            # Check for cancellation (fallback)
            if should_stop and should_stop():
                logger.log(f"[{model_cfg.alias}] Collection stopped by user.")
                progress.status = "Stopped"
                progress_callback(progress)
                break

            question = entry.get("question", "")
            
            # Prepare result entry preserving original data
            result_entry = entry.copy()
            
            try:
                # Sequential execution for short and long to be safe and simple
                # Short response
                short_resp = await get_response(question, short_max_tokens)
                result_entry["short_response"] = short_resp
                
                # Long response
                long_resp = await get_response(question, long_max_tokens)
                result_entry["long_response"] = long_resp
                
                # Add to collected data
                collected_data[doc_idx].append(result_entry)
                
            except Exception as e:
                error_msg = str(e)
                logger.log(f"[{model_cfg.alias}] Error on doc {doc_idx}, q {q_idx}: {error_msg}")
                missing_responses.append({
                    "doc_idx": doc_idx,
                    "q_idx": q_idx,
                    "question": question,
                    "error": error_msg
                })
            
            # Update progress
            progress.completed += 1
            progress_callback(progress)
            
            # Small yield to ensure UI updates if running in same loop (though this is async)
            await asyncio.sleep(0)

    except asyncio.CancelledError:
        logger.log(f"[{model_cfg.alias}] Collection task cancelled.")
        progress.status = "Stopped"
        progress_callback(progress)
        return collected_data, missing_responses

    progress.status = "Completed"
    progress_callback(progress)
    logger.log(f"[{model_cfg.alias}] Collection finished. {len(missing_responses)} missing.")
    
    return collected_data, missing_responses

async def test_provider(model_cfg: ModelConfig) -> Tuple[bool, str]:
    """
    Tests a provider configuration by sending a simple "Hi" message.
    """
    client = make_client(model_cfg)
    try:
        await client.chat.completions.create(
            model=model_cfg.model_name,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return True, "Test passed ✓"
    except Exception as e:
        return False, f"Error: {str(e)} ✗"
