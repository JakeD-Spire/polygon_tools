import json
import conversions
from vessels_api_request import vessels_api_request


# CONSTANTS
INPUT_FILE = "results/normalization_investigation/polygon1_norm.txt"
FORMAT = "wkt"
FIX = False

_, _, filename = INPUT_FILE.rpartition('/')
FILENAME = filename.split('.')[0]
FILEPATH = INPUT_FILE.split('.')[0]


def create_geojson_file(input_file, format, fix):

    query_modified = False

    if fix:
        # Convert to WKT, apply the fix, and convert back to GraphQL
        if format == "graphql":
            with open(input_file, "r") as file:
                query = file.read()
            wkt = conversions.graphql_to_wkt(query)
            wkt = conversions.process_wkt_string(wkt, "wkt", True)
            query = conversions.wkt_to_graphql(wkt, FILENAME)
            query_modified = True

        # Open WKT, apply the fix, and convert to GraphQL
        elif format == "wkt":
            with open(input_file, "r") as wkt_file:
                wkt = wkt_file.read().strip()
            wkt = conversions.process_wkt_string(wkt, "wkt", True)
            query = conversions.wkt_to_graphql(wkt, FILENAME)
            query_modified = True

    else:
        # Open WKT, Convert to GraphQL
        if format == "wkt":
            with open(input_file, "r") as wkt_file:
                wkt = wkt_file.read().strip()
            query = conversions.wkt_to_graphql(wkt, FILENAME)
            query_modified = True

        # Run as is, generate a WKT
        elif format == "graphql":
            with open(input_file, "r") as file:
                query = file.read()
            wkt = conversions.graphql_to_wkt(query)

    # Save the new query if it was modified
    if query_modified:
        query_file = FILEPATH + "_modified.graphql"
        with open(query_file, "w") as f:
            f.write(query)

    # Run the query and get the data
    output_data = vessels_api_request(query)
    output_data = json.loads(output_data)

    # Save the response data
    output_file = FILEPATH + "_data.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    # Process the final GeoJSON collection
    polygon = conversions.process_wkt_string(wkt, "geojson", False)
    vessels = conversions.process_vessel_points(output_data)
    output = {
        "type": "FeatureCollection",
        "features": [polygon] + vessels,
    }
    return output


if __name__ == "__main__":
    json_data = create_geojson_file(INPUT_FILE, FORMAT, FIX)
    if FIX:
        result_file = FILEPATH + "_result_fixed.json"
    else:
        result_file = FILEPATH + "_result.json"

    with open(result_file, "w") as f:
        json.dump(json_data, f, indent=2)
