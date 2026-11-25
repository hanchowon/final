import os
import random
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Today's Roulette API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MENUS = {
    "home": [
        {"title": "따뜻한 유부 우동 한 그릇", "budget": "예산 0원~1만원", "tag": "집콕 모드"},
        {"title": "편의점 어묵탕과 삼각김밥", "budget": "예산 1만원 이하", "tag": "집콕 모드"},
        {"title": "계란찜과 김밥", "budget": "예산 1만원 이하", "tag": "집콕 모드"},
    ],
    "walk": [
        {"title": "동네 카페 아이스 아메리카노와 소금빵", "budget": "예산 1만원 이하", "tag": "산책 가능"},
        {"title": "분식집 떡볶이 반인분", "budget": "예산 1만원 이하", "tag": "산책 가능"},
    ],
    "any": [
        {"title": "편의점 신상 디저트 하나", "budget": "예산 1만원 이하", "tag": "무난 모드"},
        {"title": "냉장고/주방에 있는 간단한 한 끼", "budget": "예산 0원", "tag": "무난 모드"},
    ],
}

MISSIONS = {
    "home": [
        {"title": "좋아하는 노래 10곡 플레이리스트 만들기", "duration": "소요시간 10분", "budget": "예산 0원"},
        {"title": "관심 가는 주식 1주 살펴보고 사기", "duration": "소요시간 10분", "budget": "소액"},
        {"title": "책상 위 안 쓰는 물건 3개 치우기", "duration": "소요시간 10분", "budget": "예산 0원"},
    ],
    "walk": [
        {"title": "평소 안 가던 골목 10분 산책하기", "duration": "소요시간 10분", "budget": "예산 0원"},
        {"title": "공원 벤치에서 하늘 사진 1장 찍기", "duration": "소요시간 10분", "budget": "예산 0원"},
    ],
    "any": [
        {"title": "좋아하는 노래 10곡 플레이리스트 만들기", "duration": "소요시간 10분", "budget": "예산 0원"},
        {"title": "관심 가는 주식 1주 살펴보고 사기", "duration": "소요시간 10분", "budget": "소액"},
    ],
}

ITEMS = {
    "home": [
        {"title": "노란색 포스트잇 & 볼펜", "badge": "행운 아이템"},
        {"title": "따뜻한 수면 양말과 립밤", "badge": "행운 아이템"},
    ],
    "walk": [
        {"title": "이어폰과 작은 에코백", "badge": "행운 아이템"},
        {"title": "손수건과 보조배터리", "badge": "행운 아이템"},
    ],
    "any": [
        {"title": "작은 메모지와 펜", "badge": "행운 아이템"},
        {"title": "향 좋은 핸드크림", "badge": "행운 아이템"},
    ],
}

ALLOWED_ADMINS = {
    email.strip().lower()
    for email in os.getenv("ADMIN_EMAILS", "admin@todayroulette.kr").split(",")
    if email.strip()
}

ALLOWED_KEYWORDS = [
    "미션", "메뉴", "소지품", "아이템", "플레이리스트", "노래", "주식",
    "산책", "운명", "뽑기", "리롤", "캘린더", "기록", "무기력", "추천", "어디", "주제"
]


class DrawRequest(BaseModel):
    energy: str = "home"
    excluded: List[str] = []


class ChatRequest(BaseModel):
    message: str
    mission_context: Optional[str] = ""


class AdminAuthRequest(BaseModel):
    email: str


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Today's Roulette API"}


@app.post("/api/draw")
def draw_cards(req: DrawRequest):
    mode = req.energy if req.energy in MENUS else "home"
    excluded_lower = [x.strip().lower() for x in req.excluded if x.strip()]

    menu_pool = [m for m in MENUS[mode] if not any(ex in m["title"].lower() for ex in excluded_lower)] or MENUS[mode]
    mission_pool = [m for m in MISSIONS[mode] if not any(ex in m["title"].lower() for ex in excluded_lower)] or MISSIONS[mode]
    item_pool = [i for i in ITEMS[mode] if not any(ex in i["title"].lower() for ex in excluded_lower)] or ITEMS[mode]

    return {
        "energy": mode,
        "menu": random.choice(menu_pool),
        "mission": random.choice(mission_pool),
        "item": random.choice(item_pool),
    }


@app.post("/api/chat")
def mission_chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        return {"reply": "죄송합니다. 안내된 주제와 관련된 질문에만 답변할 수 있습니다."}

    if not any(k in msg.lower() for k in ALLOWED_KEYWORDS):
        return {"reply": "죄송합니다. 안내된 주제와 관련된 질문에만 답변할 수 있습니다."}

    if "플레이리스트" in msg or "노래" in msg:
        reply = "누워서도 가볍게 고를 수 있는 '비 오는 날 새벽 감성 10곡'이나 '기분 전환용 업비트 10곡' 테마로 10곡만 딱 골라보세요."
    elif "어디" in msg:
        reply = "무리하지 말고 집 안 소파·책상이나 집에서 도보 5~10분 이내 가까운 곳에서 바로 시작해 보세요."
    else:
        reply = f"오늘의 선택({req.mission_context or '소소한 미션'})을 부담 없이 10분만 가볍게 해보세요. 못 해도 괜찮아요!"

    return {"reply": reply}


@app.post("/api/admin/auth")
def verify_admin(req: AdminAuthRequest):
    normalized = req.email.strip().lower()
    if normalized in ALLOWED_ADMINS:
        return {"authorized": True, "email": normalized}
    return {"authorized": False, "message": "허가된 관리자 이메일 계정이 아닙니다."}
