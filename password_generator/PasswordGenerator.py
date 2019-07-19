import hashlib
import random
import string
import itertools

class PasswordGenerator:
    def __init__(self):
        self.__additionalTokens__ = [self.__getPepper__, self.__getSalt__]
        self.__PASSWORD_LENGTH__ = 8 #random.randint(16, 32) #second param cannot be greater than length of printableCharacters array
        
    def __shuffleCharacters__(self, charSet):
        array = list(map(lambda char: ord(char), charSet))
        random.shuffle(array)
        return array

    def __shuffleCharactersToComputeHash__(self):
        array = bytearray(range(256))
        random.shuffle(array)
        return array

    def __shufflePrintableCharacters__(self):
        extraChars = r'~`!@#$%^&*()+=_-{}[]\|:;”’?/<>,.' #add more characters to printableCharacters[only if password input support it] ex. r'~`!@#$%^&*()+=_-{}[]\|:;”’?/<>,.®¯¨§¥£¢¡'
        return self.__shuffleCharacters__(string.ascii_letters + string.digits + extraChars)

    def __getSalt__(self):
        possibleValues = self.__shuffleCharactersToComputeHash__()
        singleDigitList = list(
                map(
                    lambda _:
                        bytes([possibleValues[random.randint(0, len(possibleValues) - 1)]]),
                    range(random.randint(10, 16))
                    )
                )
        return b''.join(singleDigitList)

    def __getPepper__(self):
        return self.__getSalt__()

    def __getMask__(self, mask):
        randAdditionalToken = random.randint(0, 1)
        firstToken = self.__additionalTokens__[randAdditionalToken]
        secondToken = self.__additionalTokens__[not randAdditionalToken]
        return bytearray(hashlib.sha3_512((firstToken() + mask + secondToken())).hexdigest(), encoding='utf-8')

    def __getMaskFirstPass__(self):
        initialMask = b''.join(list(map(lambda _: self.__additionalTokens__[random.randint(0, 1)](), range(random.randint(5, 10)))))
        return self.__getMask__(initialMask)

    def __repeat__(self):
        partial = self.__getMaskFirstPass__()
        for _ in range(random.randint(1000, 10000)):
            partial = self.__getMask__(partial)
        begin = random.randint(0, len(partial) - 1)
        end = begin + self.__PASSWORD_LENGTH__
        tmp_mask = b''
        if(end > len(partial) - 1):
            tmp_mask = partial[begin: 128]
            rest = end - 128
            tmp_mask += partial[0: rest]
        else:
            tmp_mask = partial[begin: end]
        return tmp_mask

    def alternative_chunks(self):
        printableCharacters = self.__shufflePrintableCharacters__()
        mask = self.__repeat__()
        result = ''
        chunks = list(
            itertools.zip_longest(
                *[iter(printableCharacters)]*((len(printableCharacters)//len(mask)))
                )
            )
        chunks = map(lambda chunk: filter(lambda isNone: isNone, chunk), chunks)
        for char in mask:
            result += chr(random.choice(list(next(chunks))))
        random.shuffle(list(result))
        return result

if __name__ == '__main__':
    for _ in range(15):
        passwordGeneratorObject = PasswordGenerator()
        password = passwordGeneratorObject.alternative_chunks()
        print('Your password:', password)
