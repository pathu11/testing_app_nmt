"""
Sinhala Fingerspelling Converter
Converts Sinhala text to fingerspelling signs following the defined rules
"""

from fingerspelling_rules import FingerspellingRules


class SinhalaFingerspellingConverter:
    """
    Main class for converting Sinhala text to fingerspelling signs
    """

    def __init__(self):
        self.rules = FingerspellingRules()

    def to_fingerspelling(self, word):
        """
        Convert a Sinhala word to fingerspelling signs
        
        Args:
            word (str): Input Sinhala word
            
        Returns:
            list: List of fingerspelling signs
            
        Raises:
            ValueError: If a sign is not in the allowed inventory
        """
        output = []

        # Clean the input word
        word = self.rules.clean_input_text(word)

        i = 0
        while i < len(word):
            ch = word[i]

            # Priority 1a: Check for Yakaranshaya pattern
            # (consonant + '්' + '‍' + 'ය' + optional vowel modifier)
            yakaranshaya_result = self._process_yakaranshaya(word, i)
            if yakaranshaya_result:
                signs, consumed_chars = yakaranshaya_result
                output.extend(signs)
                i += consumed_chars
                continue

            # Priority 1b: Check for Rakaranshaya pattern  
            # (consonant + '්' + '‍' + 'ර' + optional vowel modifier)
            rakaranshaya_result = self._process_rakaranshaya(word, i)
            if rakaranshaya_result:
                signs, consumed_chars = rakaranshaya_result
                output.extend(signs)
                i += consumed_chars
                continue

            # Priority 2: Consonant + Vowel Modifier
            consonant_vowel_result = self._process_consonant_vowel(word, i)
            if consonant_vowel_result:
                signs, consumed_chars = consonant_vowel_result
                output.extend(signs)
                i += consumed_chars
                continue

            # Priority 3: Consonant + hal mark + optional vowel
            consonant_hal_result = self._process_consonant_hal(word, i)
            if consonant_hal_result:
                signs, consumed_chars = consonant_hal_result
                output.extend(signs)
                i += consumed_chars
                continue

            # Priority 3b: Consonant + another consonant (inherent vowel)
            consonant_consonant_result = self._process_consonant_consonant(word, i)
            if consonant_consonant_result:
                signs, consumed_chars = consonant_consonant_result
                output.extend(signs)
                i += consumed_chars
                continue

            # Priority 4: Skip standalone marks
            if self._should_skip_character(ch):
                i += 1
                continue

            # Priority 5: Handle individual characters
            individual_result = self._process_individual_character(word, i, ch)
            if individual_result:
                signs, consumed_chars = individual_result
                output.extend(signs)
                i += consumed_chars
                continue

            # If we reach here, the character wasn't handled
            raise ValueError(f"Unhandled character '{ch}' in word '{word}'")

        return output

    def _process_yakaranshaya(self, word, i):
        """Process Yakaranshaya pattern: consonant + '්' + '‍' + 'ය' + optional vowel"""
        if (i + 3 < len(word) and 
            self.rules.is_sinhala_consonant(word[i]) and
            word[i+1] == self.rules.HAL_MARK and
            word[i+2] == self.rules.ZERO_WIDTH_JOINER and
            word[i+3] == 'ය'):
            
            ch = word[i]
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            
            # Validate and add consonant hal form
            self.rules.validate_sign(consonant_hal, word)
            signs = [consonant_hal]
            
            # Add Yakaranshaya sign
            self.rules.validate_sign(self.rules.YAKARANSHAYA, word)
            signs.append(self.rules.YAKARANSHAYA)
            
            consumed = 4  # consonant + ් + ‍ + ය
            
            # Check for trailing vowel modifier
            if (i + 4 < len(word) and word[i+4] in self.rules.VOWEL_MAP):
                independent_vowel = self.rules.VOWEL_MAP[word[i+4]]
                self.rules.validate_sign(independent_vowel, word)
                signs.append(independent_vowel)
                consumed = 5
                
            return signs, consumed
        return None

    def _process_rakaranshaya(self, word, i):
        """Process Rakaranshaya pattern: consonant + '්' + '‍' + 'ර' + optional vowel"""
        if (i + 3 < len(word) and 
            self.rules.is_sinhala_consonant(word[i]) and
            word[i+1] == self.rules.HAL_MARK and
            word[i+2] == self.rules.ZERO_WIDTH_JOINER and
            word[i+3] == 'ර'):
            
            ch = word[i]
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            
            # Validate and add consonant hal form
            self.rules.validate_sign(consonant_hal, word)
            signs = [consonant_hal]
            
            # Add Rakaranshaya sign
            self.rules.validate_sign(self.rules.RAKARANSHAYA, word)
            signs.append(self.rules.RAKARANSHAYA)
            
            consumed = 4  # consonant + ් + ‍ + ර
            
            # Check for trailing vowel modifier
            if (i + 4 < len(word) and word[i+4] in self.rules.VOWEL_MAP):
                independent_vowel = self.rules.VOWEL_MAP[word[i+4]]
                self.rules.validate_sign(independent_vowel, word)
                signs.append(independent_vowel)
                consumed = 5
                
            return signs, consumed
        return None

    def _process_consonant_vowel(self, word, i):
        """Process consonant + vowel modifier pattern"""
        if (self.rules.is_sinhala_consonant(word[i]) and 
            i + 1 < len(word) and word[i+1] in self.rules.VOWEL_MAP):
            
            ch = word[i]
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            independent_vowel = self.rules.VOWEL_MAP[word[i+1]]
            
            self.rules.validate_sign(consonant_hal, word)
            self.rules.validate_sign(independent_vowel, word)
            
            return [consonant_hal, independent_vowel], 2
        return None

    def _process_consonant_hal(self, word, i):
        """Process consonant + hal mark + optional vowel pattern"""
        if (self.rules.is_sinhala_consonant(word[i]) and 
            i + 1 < len(word) and word[i+1] == self.rules.HAL_MARK):
            
            ch = word[i]
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            self.rules.validate_sign(consonant_hal, word)
            
            signs = [consonant_hal]
            consumed = 2  # consonant + ්
            
            # Check for vowel modifier after hal mark
            if (i + 2 < len(word) and word[i+2] in self.rules.VOWEL_MAP):
                independent_vowel = self.rules.VOWEL_MAP[word[i+2]]
                self.rules.validate_sign(independent_vowel, word)
                signs.append(independent_vowel)
                consumed = 3
                
            return signs, consumed
        return None

    def _process_consonant_consonant(self, word, i):
        """Process consonant followed by another consonant (inherent vowel)"""
        if (self.rules.is_sinhala_consonant(word[i]) and 
            i + 1 < len(word) and self.rules.is_sinhala_consonant(word[i+1])):
            
            ch = word[i]
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            
            self.rules.validate_sign(consonant_hal, word)
            self.rules.validate_sign(self.rules.INHERENT_VOWEL, word)
            
            return [consonant_hal, self.rules.INHERENT_VOWEL], 1
        return None

    def _should_skip_character(self, ch):
        """Check if character should be skipped"""
        return ch in [self.rules.HAL_MARK, self.rules.ZERO_WIDTH_JOINER]

    def _process_individual_character(self, word, i, ch):
        """Process individual characters"""
        # Vowel modifier -> independent vowel
        if ch in self.rules.VOWEL_MAP:
            sign = self.rules.VOWEL_MAP[ch]
            self.rules.validate_sign(sign, word)
            return [sign], 1
            
        # Sinhala consonant -> hal form + inherent vowel
        elif self.rules.is_sinhala_consonant(ch):
            consonant_hal = self.rules.get_consonant_hal_form(ch)
            self.rules.validate_sign(consonant_hal, word)
            self.rules.validate_sign(self.rules.INHERENT_VOWEL, word)
            return [consonant_hal, self.rules.INHERENT_VOWEL], 1
            
        # Other characters (independent vowels, etc.)
        else:
            self.rules.validate_sign(ch, word)
            return [ch], 1

    def batch_convert(self, words):
        """
        Convert multiple words to fingerspelling
        
        Args:
            words (list): List of Sinhala words
            
        Returns:
            dict: Dictionary mapping words to their fingerspelling signs
        """
        results = {}
        for word in words:
            try:
                results[word] = self.to_fingerspelling(word)
            except ValueError as e:
                results[word] = {"error": str(e)}
        return results