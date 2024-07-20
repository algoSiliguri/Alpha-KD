import json


def load_instruments(file_path):
    """Load instruments data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def process_instruments(instruments_data):
    """Process the instruments data to extract required information."""
    data = []
    for instrument in instruments_data:
        if instrument["segment"] == "NSE_EQ":
            instrumentkey = instrument["instrument_key"]
            data.append({instrument["trading_symbol"].strip(): instrumentkey})

    return data


def save_to_file(data, file_path):
    """Save the processed data to a json file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def main():
    # Load instruments data
    instruments_data = load_instruments('instruments.json')

    # Process instruments data
    processed_data = process_instruments(instruments_data)

    # Save processed data to a json file
    save_to_file(processed_data, 'instrumentsData.json')


if __name__ == "__main__":
    main()
