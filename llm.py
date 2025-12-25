"""
LLM 통합 모듈
OpenAI 및 Gemini API를 사용한 RAG 질문 답변
"""
import requests


def get_ai_answer(query, context_docs, provider, api_key, model_name):
    """
    검색 결과를 기반으로 LLM을 사용하여 질문에 답변합니다.
    REST API를 직접 호출하여 경량화합니다.
    """
    try:
        # 컨텍스트 구성
        context = "\n\n".join([f"[문서 {i+1}] {doc['text']}" for i, doc in enumerate(context_docs)])
        
        # RAG 프롬프트
        system_prompt = """당신은 문서 기반 질문 답변 시스템입니다. 
제공된 문서 내용을 바탕으로 사용자의 질문에 답변하세요.

중요한 규칙:
1. 반드시 한국어로 답변하세요.
2. 제공된 문서에 답변이 있으면 해당 내용을 바탕으로 명확하고 친절하게 설명하세요.
3. 제공된 문서에 답변이 없거나 불확실하면 "죄송합니다. 제공된 문서에서 관련 정보를 찾을 수 없습니다."라고 답변하세요.
4. 추측하거나 문서에 없는 내용을 만들어내지 마세요.
5. 답변은 2-3문장으로 간결하게 작성하세요."""

        user_prompt = f"""질문: {query}

참고 문서:
{context}

위 문서를 바탕으로 질문에 답변해주세요."""

        if provider == "OpenAI":
            # OpenAI REST API 호출
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            return answer, None
            
        elif provider == "Gemini":
            # Gemini REST API 호출
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [{
                        "parts": [{"text": full_prompt}]
                    }]
                },
                timeout=30
            )
            response.raise_for_status()
            answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return answer, None
        
        else:
            return None, "지원하지 않는 AI 제공자입니다."
        
    except requests.exceptions.Timeout:
        return None, "요청 시간이 초과되었습니다. 다시 시도해주세요."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return None, "API 키가 올바르지 않습니다. 확인 후 다시 시도해주세요."
        elif e.response.status_code == 429:
            return None, "API 사용량 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        else:
            return None, f"API 오류 ({e.response.status_code}): {e.response.text}"
    except Exception as e:
        return None, f"답변 생성 중 오류가 발생했습니다: {str(e)}"
