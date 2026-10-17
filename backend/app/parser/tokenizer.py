from app.parser.types import AddressToken


def tokenize_address(normalized_address: str) -> list[AddressToken]:
    tokens: list[AddressToken] = []
    for index, part in enumerate(normalized_address.split(",")):
        text = part.strip(" .")
        if not text:
            continue
        tokens.append(AddressToken(index=index, text=text, words=tuple(text.split())))
    return tokens
