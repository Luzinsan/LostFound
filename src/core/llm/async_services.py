import logging
import json
import aiohttp
import asyncio
import re
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.back.models.rag_models import ChatMessage, LLM_MODEL


async def chutes_api_rephrase_query(
        query: str, 
        max_tokens: int = 800
    ) -> Dict[str, Any]:
    """
    Uses Chutes API to rephrase the query and extract cities.
    Returns a dictionary with "rephrased_query" and "cities" keys.
    """
    default_response = {"rephrased_query": query, "cities": None}
    try:
        prompt = settings.QUERY_REPHRASE_PROMPT.format(query=query)
        headers = {
            "Authorization": f"Bearer {settings.CHUTES_API_KEY}",
            "Content-Type": "application/json"
        }
        request_data = {
            "model": "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.CHUTES_LLM_API_URL,
                headers=headers,
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"API error during rephrasing: {response.status} {error_text}")
                    return default_response
                
                response_data = await response.json()
                generated_text = (
                    response_data
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if not generated_text:
                    logging.warning("LLM returned empty content for rephrasing.")
                    return default_response
                try:
                    parts = generated_text.split("|||")
                    if len(parts) == 2:
                        rephrased_query = parts[0].strip()
                        cities = parts[1].strip()
                        if cities == "NONE":
                            cities = None
                        return {
                            "rephrased_query": rephrased_query,
                            "cities": cities
                        }
                    else:
                        logging.error(f"Invalid format in LLM response: {generated_text}")
                        return default_response
                except Exception as e:
                    logging.error(f"Error processing LLM response for rephrasing: {str(e)}. Response was: {generated_text}")
                    return default_response
    except Exception as e:
        logging.error(f"Query rephrasing error: {str(e)}")
        return default_response


async def generate_rag_response(messages: List[ChatMessage], temperature: float = 0.7, max_tokens: int = 500) -> str:
    """
    Generate a response using the LLM based on provided messages (non-streaming).
    """
    try:
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        headers = {
            "Authorization": f"Bearer {settings.CHUTES_API_KEY}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": LLM_MODEL,
            "messages": api_messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.CHUTES_LLM_API_URL,
                headers=headers,
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"API error: {error_text}")
                    return f"Error communicating with LLM API: {error_text}"
                
                response_data = await response.json()
                print("response_data: ", response_data)
                return response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        logging.error(f"RAG response generation error: {str(e)}")
        return f"Error generating response: {str(e)}"

async def stream_rag_response(messages: List[ChatMessage], temperature: float = 0.7, max_tokens: int = 500):
    """
    Stream a response from the LLM API based on provided messages.
    """
    try:
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        headers = {
            "Authorization": f"Bearer {settings.CHUTES_API_KEY}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": LLM_MODEL,
            "messages": api_messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.CHUTES_LLM_API_URL,
                headers=headers,
                json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"API error: {error_text}")
                    yield f"data: {json.dumps({'error': f'API error: {error_text}'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        
                        try:
                            json_data = json.loads(data)
                            content = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                        except json.JSONDecodeError:
                            if data.strip():
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': data}}]})}\n\n"
                        except Exception as e:
                            logging.error(f"Error parsing chunk: {e}")
                
                yield f"data: [DONE]\n\n"
    except Exception as e:
        logging.error(f"Streaming RAG generation error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield f"data: [DONE]\n\n"