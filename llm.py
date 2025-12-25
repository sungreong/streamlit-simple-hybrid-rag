import json
import re
import requests

def get_ai_answer(query, context_docs, provider, api_key, model_name):
    """
    검색 결과를 기반으로 LLM을 사용하여 질문에 답변합니다.
    REST API를 직접 호출하여 경량화합니다.
    JSON 형식으로 구조화된 답변(답변 내용 + 출처)을 반환합니다.
    """
    try:
        # 컨텍스트 구성 (ID 포함)
        context_entries = []
        for doc in context_docs:
            entry = f"ID: {doc['chunk_id']}\n내용: {doc['text']}"
            context_entries.append(entry)
        
        context = "\n\n---\n\n".join(context_entries)
        
        # RAG 프롬프트 (JSON 출력 강제)
        system_prompt = """당신은 문서 기반 질문 답변 시스템입니다. 
제공된 문서 내용을 바탕으로 사용자의 질문에 답변하세요.

반드시 다음 JSON 형식으로만 응답해야 합니다:
{
    "answer": "질문에 대한 명확하고 친절한 답변 (마크다운 형식 지원)",
    "references": ["참고한 문서의 ID 목록 (예: chunk_1, chunk_5)"]
}

중요 규칙:
1. 반드시 한국어로 답변하세요.
2. 'answer' 필드에는 본문 텍스트만 포함하세요.
3. 'references' 필드에는 답변을 작성하는 데 실제로 도움이 된 문서의 ID만 포함하세요.
4. 문서에 답변이 없으면 "answer"에 "죄송합니다. 제공된 문서에서 관련 정보를 찾을 수 없습니다."라고 적고 "references"는 빈 리스트로 둡니다.
5. 추측하지 말고 문서 내용에 기반해서만 답변하세요."""

        user_prompt = f"""질문: {query}

참고 문서:
{context}

위 문서를 바탕으로 질문에 답변하고 참고한 문서 ID를 JSON으로 반환해주세요."""

        answer_json = None

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
                    "max_tokens": 1000,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
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
                    # Gemini는 response_mime_type을 지원하지만 모델 버전에 따라 다르므로 텍스트 파싱 사용
                },
                timeout=30
            )
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        else:
            return None, "지원하지 않는 AI 제공자입니다."

        # JSON 파싱
        try:
            # 마크다운 코드 블록 제거 (Gemini 등이 ```json ... ``` 으로 감쌀 경우)
            if "```" in content:
                content = re.sub(r"```json|```", "", content).strip()
            
            parsed_result = json.loads(content)
            
            # 구조 검증
            if "answer" not in parsed_result:
                parsed_result["answer"] = content
            if "references" not in parsed_result:
                parsed_result["references"] = []
                
            return parsed_result, None
            
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 일반 텍스트로 처리
            return {"answer": content, "references": []}, None
        
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
