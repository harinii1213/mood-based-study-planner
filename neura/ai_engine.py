from transformers import pipeline

# ============================================================
# NEURA AI ENGINE
# ============================================================

print("Loading Neura AI model...")

model = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-0.5B-Instruct"
)

print("Neura AI model loaded successfully!")


# ============================================================
# NEURA DECISION LOGIC
# ============================================================

def select_study_activity(mood, energy, priority):

    energy = int(energy)

    if mood == "Tired" or energy < 40:

        if priority == "High":
            return {
                "activity": "Review the key concepts",
                "duration": "10-15 minutes",
                "difficulty": "Easy"
            }

        return {
            "activity": "Review the basic concepts",
            "duration": "10-15 minutes",
            "difficulty": "Easy"
        }

    elif mood == "Stressed" or 40 <= energy <= 70:

        if priority == "High":
            return {
                "activity": "Practice a few important questions",
                "duration": "20-25 minutes",
                "difficulty": "Moderate"
            }

        return {
            "activity": "Learn and practice the main concepts",
            "duration": "20-30 minutes",
            "difficulty": "Moderate"
        }

    else:

        if priority == "High":
            return {
                "activity": "Solve challenging problems",
                "duration": "30-45 minutes",
                "difficulty": "Challenging"
            }

        return {
            "activity": "Study and apply the main concepts",
            "duration": "30-45 minutes",
            "difficulty": "Challenging"
        }


# ============================================================
# NEXT BEST ACTION
# ============================================================

def generate_study_recommendation(
    mood,
    energy,
    task,
    priority
):

    decision = select_study_activity(
        mood,
        energy,
        priority
    )

    activity = decision["activity"]
    duration = decision["duration"]

    prompt = f"""
You are Neura, an AI study assistant.

Create ONE short study recommendation.

TASK:
{task}

STUDENT MOOD:
{mood}

ENERGY:
{energy}/100

PRIORITY:
{priority}

NEURA DECISION:

ACTIVITY:
{activity}

DURATION:
{duration}

Rules:

1. Stay directly related to the task.
2. Do not change the selected activity.
3. Do not suggest exercise, food, sleeping or meditation.
4. Mention the duration.
5. Keep the answer concise.
6. Give only ONE recommendation.

Return:

Study activity: <specific activity related to the task>
Duration: <duration>
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:

        result = model(
            messages,
            max_new_tokens=80,
            do_sample=False
        )

        response = result[0]["generated_text"][-1]["content"]
        response = response.strip()

        if not response:
            raise ValueError("Empty AI response")

        return response

    except Exception as e:

        print("Neura Next Best Action error:", e)

        return (
            f"Study activity: {activity} related to '{task}'.\n"
            f"Duration: {duration}"
        )


# ============================================================
# NEURA COPILOT CHAT
# ============================================================

def generate_chat_response(message):

    prompt = f"""
You are Neura, an AI study assistant for students.

Answer the student's question clearly and accurately.

Student question:
{message}

Rules:

1. Answer the question directly.
2. Use simple language.
3. Be helpful for learning.
4. If the question is technical, explain it with a simple example when useful.
5. Keep the answer concise.
6. Do not talk about being a local model.
7. Do not mention API keys.
8. Do not give unrelated study recommendations unless asked.

Answer:
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:

        result = model(
            messages,
            max_new_tokens=180,
            do_sample=False
        )

        response = result[0]["generated_text"][-1]["content"]
        response = response.strip()

        if not response:
            raise ValueError("Empty AI response")

        return response

    except Exception as e:

        print("Neura Copilot error:", e)

        return (
            "I'm having trouble generating an answer "
            "right now. Please try again."
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("TEST — NEXT BEST ACTION")
    print("========================================")

    print(
        generate_study_recommendation(
            mood="Tired",
            energy=28,
            task="What is AI?",
            priority="Low"
        )
    )

    print("\n========================================")
    print("TEST — NEURA COPILOT")
    print("========================================")

    print(
        generate_chat_response(
            "What is AI?"
        )
    )

    print("\n========================================")
    print("NEURA AI TEST COMPLETE")
    print("========================================")