import re
import geojson
import antimeridian
from shapely import wkt, geometry


def polygon_to_graphql(polygon):
    """Convert Shapely Polygon/Multipolygon to GraphQL format"""

    # Ensure it is a MultiPolygon for uniformity
    if isinstance(polygon, geometry.Polygon):
        polygon = geometry.MultiPolygon([polygon])

    # Build the GraphQL-compatible GeoJSON structure
    coordinates = []
    for poly in polygon.geoms:
        poly_coords = []
        for ring in poly.exterior.coords:
            # Convert each coordinate to a [lon, lat] pair
            poly_coords.append([ring[0], ring[1]])
        # Wrap each set of polygon rings as needed
        coordinates.append([poly_coords])

    return {
        "type": "MultiPolygon",
        "coordinates": coordinates
    }


def process_wkt_string(wkt_string, format, fix):
    """Convert a WKT to graphQL or GeoJSON
    (optionally, apply antimeridian fix)"""
    # Convert WKT to Shapely Polygon, apply antimeridian fix
    polygon = wkt.loads(wkt_string)
    if fix:
        polygon = antimeridian.fix_polygon(polygon)

    if format == "wkt":
        return polygon.wkt

    elif format == "graphql":
        return polygon_to_graphql(polygon)

    elif format == "geojson":
        return geojson.Feature(
            geometry=geojson.loads(
                geojson.dumps(polygon.__geo_interface__)
                )
            )

    else:
        raise ValueError("format must be \"wkt\", \"graphql\", or \"geojson\"")


def wkt_to_graphql(wkt, query_name):
    """Generates a GraphQL query from a WKT string"""

    def parse_coordinates(wkt):
        """Parses WKT into a list of polygons with coordinates."""
        if wkt.startswith("POLYGON"):
            # Extract the coordinates part of the WKT (inside parentheses)
            coordinates_part = wkt.strip().lstrip("POLYGON((").rstrip("))")
            return [
                [
                    [float(coord) for coord in pair.split()]
                    for pair in coordinates_part.split(",")
                ]
            ]
        elif wkt.startswith("MULTIPOLYGON"):
            # Extract the MULTIPOLYGON part and split into individual polygons
            coordinates_part = wkt.strip().lstrip(
                "MULTIPOLYGON ((("
                ).rstrip(")))")
            polygons = coordinates_part.split(")), ((")
            return [
                [
                    [float(coord) for coord in pair.split()]
                    for pair in polygon.split(",")
                ]
                for polygon in polygons
            ]
        else:
            raise ValueError(f"Unsupported WKT type: {wkt.split(' ')[0]}")

    # Parse the WKT string
    polygons = parse_coordinates(wkt)

    # Determine the GraphQL type based on the number of polygons
    if len(polygons) > 1:
        aoi_type = "multiPolygon"
        graphql_type = "MultiPolygon"
        graphql_coordinates = ",\n".join(
            f"[[{', '.join(f'[{lon}, {lat}]' for lon, lat in polygon)}]]"
            for polygon in polygons
        )
    else:
        aoi_type = "polygon"
        graphql_type = "Polygon"
        graphql_coordinates = ",\n".join(
            f"[{', '.join(f'[{lon}, {lat}]' for lon, lat in polygon)}]"
            for polygon in polygons
        )

    # Template for the GraphQL query
    graphql_template = f"""query {query_name} {{
        vessels(
            first: 1000,
            areaOfInterest: {{
                {aoi_type}: {{
                    type: "{graphql_type}"
                    coordinates: [
                        {graphql_coordinates}
                    ]
                }}
            }}
        ) {{
            pageInfo {{
                hasNextPage
                endCursor
            }}
            totalCount {{
                relation
                value
            }}
            nodes {{
                lastPositionUpdate {{
                    latitude
                    longitude
                }}
            }}
        }}
    }}"""
    return graphql_template


def graphql_to_wkt(query):
    """Extract the Polygon from a GraphQL query and return it in WKT format"""

    # Regex pattern to extract the coordinates block
    pattern = r"coordinates:\s*\[\s*\[(.*?)\]\s*\]"
    match = re.search(pattern, query, re.DOTALL)

    if not match:
        raise ValueError("Polygon coordinates not found in the GraphQL query.")

    # Extract coordinates block and clean it up
    coordinates_block = match.group(1).strip()

    # Split into individual coordinate pairs
    coordinate_lines = re.findall(r"\[([^]]+)\]", coordinates_block)

    # Parse coordinates into a list of tuples
    coordinates = []
    for line in coordinate_lines:
        lon, lat = map(float, line.split(","))
        coordinates.append((lon, lat))

    # Ensure the polygon is closed (last point equals first point)
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    # Convert coordinates to WKT format
    wkt_coordinates = ', '.join(f"{lon} {lat}" for lon, lat in coordinates)
    wkt = f"POLYGON(({wkt_coordinates}))"

    return wkt


def process_vessel_points(data):
    """Extract vessel coordinates from a GraphQL response JSON"""

    # Iterate over each node in the JSON data
    features = []
    for node in data["data"]["vessels"]["nodes"]:
        # Extract latitude and longitude
        latitude = node["lastPositionUpdate"]["latitude"]
        longitude = node["lastPositionUpdate"]["longitude"]

        # Create a GeoJSON Point feature
        # GeoJSON uses (longitude, latitude)
        point_feature = geojson.Feature(
            geometry=geojson.Point((longitude, latitude)),
            properties={}
        )

        # Add the point feature to the list
        features.append(point_feature)

    return features
