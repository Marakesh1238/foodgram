MAX_LENGTH = 256
MAX_EMAIL_FIELD = 254
MAX_NAME_FIELD = 150
CONFIRM_CODE_LEN = 32
PER_PAGE = 10
MAX_PER_PAGE = 100
RESOLVED_CHARS = (
    'Допустимы только латинские буквы, '
    'цифры и символы @/./+/-/_. '
)
FORBIDDEN_NAME = 'Имя пользователя \'me\' использовать нельзя!'
HELP_TEXT_NAME = RESOLVED_CHARS + FORBIDDEN_NAME
UNIQUE_FIELDS = {
    'unique': 'Пользователь с таким ником уже существует.',
}
MAX_PAS = 100
MAX_MEASURENENT_UNUT = 20
