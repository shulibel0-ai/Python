import random

# Word bank
word_bank = ['salame', 'fideos', 'pizza', 'hamburguesa', 'banana']
word = random.choice(word_bank)

# List of single-character placeholders
guessedWord = ['_'] * len(word)
attempts = 10

while attempts > 0:
    print('\nCurrent word: ' + ' '.join(guessedWord))
    guess = input('Guess a letter: ').lower().strip()

    if not guess:
        print('Please enter a letter.')
        continue
    if len(guess) != 1:
        print('Please enter a single letter.')
        continue

    if guess in word:
        found = False
        for i, ch in enumerate(word):
            if ch == guess:
                guessedWord[i] = guess
                found = True
        if found:
            print('Great guess!')
    else:
        attempts -= 1
        print('Wrong guess! Attempts left: ' + str(attempts))

    if '_' not in guessedWord:
        print('\nCongratulations!! You guessed the word: ' + word)
        break

if attempts == 0 and '_' in guessedWord:
    print('\nYou ran out of attempts! The word was: ' + word)
