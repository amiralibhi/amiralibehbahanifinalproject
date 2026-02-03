from google import genai
import os
import re
import concurrent.futures


# ====== API KEY ======
os.environ["GEMINI_API_KEY"] = "AIzaSyBFrAxLXo81Fq0bpVidV32oIiIEMTLDrKI"

# ====== Init client ======
client = genai.Client()

def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# ====== SESSION STATE ======
class SessionState:
    def init(self):
        self.preferences = {}   
        self.history = []       
        self.itinerary = ""     


state = SessionState()

# ====== SECURITY CALLBACK ======
FORBIDDEN_WORDS = ["مرز", "خطرناک", "قاچاق", "جنگ"]

def security_check(user_input):
    for word in FORBIDDEN_WORDS:
        if word in user_input:
            return False, "❌ درخواست شما به دلایل امنیتی مسدود شد."
    return True, ""

# ====== GATEKEEPER AGENT ======
def extract_preferences(text):
    prefs = {}
    if "گیاهخوار" in text:
        prefs["diet"] = "vegetarian"
    if "پیاده" in text:
        prefs["transport"] = "walking"
    if "میلیون" in text:
        nums = re.findall(r'\d+', text)
        if nums:
            prefs["budget"] = int(nums[0])
    if "چهارروزه" in text:
        prefs["days"] = 4
    elif "۲ روزه" in text or "2 روزه" in text:
        prefs["days"] = 2
    elif "۱ روزه" in text or "1 روزه" in text:
        prefs["days"] = 1
    if "تهران" in text:
        prefs["city"] = "تهران"
    if "اصفهان" in text:
        prefs["city"] = "اصفهان"
    return prefs

# ====== PARALLEL RESEARCH AGENTS ======
def attraction_agent(prefs):
    return ask_gemini(f"جاذبه‌های تاریخی مهم شهر {prefs.get('city')} را با توضیح کوتاه معرفی کن.")

def food_agent(prefs):
    if prefs.get("diet") == "vegetarian":
        return ask_gemini(f"رستوران‌های گیاهخواری معروف در {prefs.get('city')} را معرفی کن.")
    return ask_gemini(f"غذاهای محلی و رستوران‌های معروف در {prefs.get('city')} را معرفی کن.")

def transport_agent(prefs):
    if prefs.get("transport") == "walking":
        return ask_gemini(f"مسیرهای پیاده‌روی گردشگری در {prefs.get('city')} را معرفی کن.")
    return ask_gemini(f"روش‌های حمل و نقل مناسب گردشگران در {prefs.get('city')} چیست؟")

def run_parallel_research(prefs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(attraction_agent, prefs)
        f2 = executor.submit(food_agent, prefs)
        f3 = executor.submit(transport_agent, prefs)
        return {
            "attractions": f1.result(),
            "food": f2.result(),
            "transport": f3.result()
        }

# ====== ITINERARY PIPELINE ======
def build_itinerary(prefs, research):
    days = prefs.get("days", 1)
    prompt = f"""
    با اطلاعات زیر یک برنامه سفر {days} روزه دقیق و زمان‌بندی شده بنویس:

    جاذبه‌ها:
    {research['attractions']}

    غذا:
    {research['food']}

    حمل و نقل:
    {research['transport']}

    بودجه: {prefs.get('budget', 'نامشخص')} میلیون تومان
    """
    return ask_gemini(prompt)

# ====== OPTIMIZATION LOOP ======
def optimize_itinerary(plan):
    for _ in range(2):
        feedback = ask_gemini(f"این برنامه سفر را نقد کن و اگر نیاز به بهبود دارد بگو:\n{plan}")
        if "عالی" in feedback or "کامل" in feedback:
            break
        plan = ask_gemini(f"بر اساس این نقد، برنامه را بهتر کن:\nنقد:\n{feedback}\nبرنامه قبلی:\n{plan}")
    return plan
# ====== MAIN SYSTEM ======
def travel_planner(user_input):
    allowed, msg = security_check(user_input)
    if not allowed:
        return msg
    state.preferences = extract_preferences(user_input)
    research = run_parallel_research(state.preferences)
    draft_plan = build_itinerary(state.preferences, research)
    final_plan = optimize_itinerary(draft_plan)
    state.itinerary = final_plan
    state.history.append(user_input)
    return final_plan
# ====== RUN LOOP ======
print("✈️ !سیستم برنامه‌ریزی هوشمند سفر آماده است\n")
while True:
    user_input = input("درخواست شما: ")
    if user_input.lower() in ["exit", "quit"]:
        print("خروج")
        break
    print("\n⏳ در حال طراحی برنامه سفر...\n")
    response = travel_planner(user_input)
    print(response)
    print("\n" + "="*50 + "\n")