def parse_percentage_input(user_input):
    """
    Converts user input into decimal format.

    Examples:
    "0.10"   -> 0.10
    "10%"    -> 0.10
    "10"     -> 0.10
    "0,10"   -> 0.10
    "10,5%"  -> 0.105
    """

    value = user_input.strip().replace(",", ".")

    if value.endswith("%"):
        value = value[:-1].strip()

    number = float(value)

    if number > 1:
        number = number / 100

    return number


def get_valid_percentage_input(prompt, min_value=0, max_value=1):
    """
    Repeatedly asks the user for input until a valid percentage is entered.
    Returns the value in decimal format.
    """

    while True:
        raw_input_value = input(prompt)

        try:
            parsed_value = parse_percentage_input(raw_input_value)

            if parsed_value < min_value or parsed_value > max_value:
                print(
                    f"Please enter a value between {min_value:.0%} and {max_value:.0%}."
                )
                continue

            return parsed_value

        except ValueError:
            print("Invalid input. Please enter a value like 10, 10%, 0.10, or 10,5%.")