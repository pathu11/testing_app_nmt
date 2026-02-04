# Sinhala Fingerspelling Rules Configuration
# This file contains all the rules and mappings for converting Sinhala text to fingerspelling

class FingerspellingRules:
    """
    Configuration class containing all rules for Sinhala fingerspelling conversion
    """
    
    # Allowed signs in the fingerspelling inventory
    ALLOWED_SIGNS = {
        # vowels
        "අ", "ආ", "ඇ", "ඈ", "ඉ", "ඊ", "උ", "ඌ", "එ", "ඒ", "ඔ", "ඕ",
        "ඓ", "ඖ", "ඍ",

        # consonants (hal)
        "ක්", "ග්", "ජ්", "ට්", "ද්", "ණ්", "ත්", "න්", "බ්", "ය්", "ල්",
        "ඩ්", "ප්", "ම්", "ර්", "ව්", "ස්", "හ්", "ළ්",
        "ඛ්", "ධ්", "ච්", "භ්", "ථ්", "ෆ්", "ශ්", "ෂ්", "ඤ්", "ඡ්",

        # special consonants
        "ඟ්", "ඳ්", "ඬ්", "ඹ්", "ඝ්", "ඪ්", "ඨ්", "ඵ්",
        "ං", "්‍ය",
        "ෟ",
        "්‍ර"  # Rakaranshaya
    }

    # Vowel mapping from modifier to independent form
    VOWEL_MAP = {
        "ා": "ආ",
        "ි": "ඉ",
        "ී": "ඊ",
        "ු": "උ",
        "ූ": "ඌ",
        "ෙ": "එ",
        "ේ": "ඒ",
        "ො": "ඔ",
        "ෝ": "ඕ",
        "ෛ": "ඓ",
        "ෞ": "ඖ",
        "ැ": "ඇ",
        "ෑ": "ඈ"
    }

    # Unicode ranges for Sinhala consonants
    SINHALA_CONSONANT_START = "\u0D9A"  # ක
    SINHALA_CONSONANT_END = "\u0DC6"    # ෆ

    # Special characters
    HAL_MARK = "්"
    ZERO_WIDTH_JOINER = "‍"
    YAKARANSHAYA = "්‍ය"
    RAKARANSHAYA = "්‍ර"
    INHERENT_VOWEL = "අ"

    # Processing priorities (for algorithm explanation)
    PRIORITIES = {
        1: "Yakaranshaya and Rakaranshaya patterns",
        2: "Consonant + vowel modifier combinations", 
        3: "Consonant + hal mark combinations",
        4: "Skip standalone marks",
        5: "Individual character processing"
    }

    @staticmethod
    def is_sinhala_consonant(char):
        """Check if a character is a Sinhala consonant"""
        return FingerspellingRules.SINHALA_CONSONANT_START <= char <= FingerspellingRules.SINHALA_CONSONANT_END

    @staticmethod
    def get_consonant_hal_form(consonant):
        """Get the hal form of a consonant"""
        return consonant + FingerspellingRules.HAL_MARK

    @staticmethod
    def clean_input_text(text):
        """Clean input text by removing unwanted characters but keeping essential joiners"""
        return text.replace('\u200b', '').replace('\ufeff', '').replace(' ', '')

    @staticmethod
    def validate_sign(sign, word):
        """Validate if a sign is in the allowed inventory"""
        if sign not in FingerspellingRules.ALLOWED_SIGNS:
            raise ValueError(f"Sign '{sign}' not in inventory for word '{word}'")
        return True