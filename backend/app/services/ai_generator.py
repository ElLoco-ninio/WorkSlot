from app.core.config import settings

class AIGeneratorService:
    @staticmethod
    def generate_profile_description(business_name: str, category: str, city: str) -> str:
        """
        Generate a professional business description.
        In production, this would call OpenAI/Anthropic/Gemini API.
        For MVP, we use templates.
        """
        templates = [
            f"Welcome to {business_name}, {city}'s premier destination for {category} services. We are dedicated to providing top-tier experiences tailored to your needs.",
            f"At {business_name}, we specialize in {category}. Located in the heart of {city}, we bring passion and expertise to every appointment.",
            f"Your trusted {category} expert in {city}. {business_name} offers professional, reliable services designed just for you."
        ]
        # Deterministic choice based on name length for stability
        import hashlib
        index = int(hashlib.md5(business_name.encode()).hexdigest(), 16) % len(templates)
        return templates[index]

    @staticmethod
    def generate_intake_questions(category: str) -> list[str]:
        """
        Generate suggested intake questions based on service category.
        """
        common_questions = [
            "What is your primary goal for this session?",
            "Do you have any specific requirements or preferences?",
            "How did you hear about us?"
        ]
        
        category_specific = {
            "Consulting": [
                "What is your current biggest business challenge?",
                "Have you worked with a consultant before?"
            ],
            "Health & Wellness": [
                "Do you have any injuries or medical conditions?",
                "Are you currently taking any medication?"
            ],
            "Education": [
                "What is your current proficiency level?",
                "What are your specific learning objectives?"
            ],
            "Home Services": [
                "Is there parking available?",
                "Do you have any pets we should be aware of?"
            ]
        }
        
        # Match partial category keys
        questions = common_questions.copy()
        for key, specific_qs in category_specific.items():
            if key.lower() in category.lower():
                questions.extend(specific_qs)
                
        return questions
        
    @staticmethod
    def generate_booking_summary(customer_name: str, service: str, time: str) -> str:
        return f"New Booking: {customer_name} for {service} at {time}"
