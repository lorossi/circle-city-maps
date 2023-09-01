import re

import toml


def format_value(value: str):
    if re.match(r"#[0-9a-fA-F]{6}", value):
        return value.upper()

    return value


def load_styles() -> dict:
    with open("styles.toml", "r") as f:
        return toml.load(f)


def save_styles(data: dict):
    with open("styles.toml", "w") as f:
        toml.dump(data, f)


def main():
    toml_data = load_styles()
    clean_data = {"Styles": []}

    for style in toml_data["Styles"]:
        clean_style = {}
        for key, value in style.items():
            if isinstance(value, list):
                clean_style[key] = [format_value(v) for v in value]
            else:
                clean_style[key] = format_value(value)

        clean_data["Styles"].append(clean_style)

    clean_data["Styles"].sort(key=lambda x: x["name"])
    save_styles(clean_data)


if __name__ == "__main__":
    main()
