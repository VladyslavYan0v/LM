import os
import struct


def write_level(filename, raw_map, start_x, start_y):
    char_to_id = {
        '.': 1,
        '#': 2,
        'D': 3,
        'O': 4,
        'P': 5,
        'I': 6,
        'X': 7,
        ' ': 0,
    }
    
    max_width = max(len(row) for row in raw_map)
    normalized_map = [row.ljust(max_width, '.') for row in raw_map]
    
    height = len(normalized_map)
    width = max_width

    file_path = os.path.join("embed", "rooms", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    portal_map = [list(row) for row in normalized_map]
    for y, row in enumerate(normalized_map):
        for x, ch in enumerate(row):
            if ch.upper() == 'P' and (x == 0 or normalized_map[y][x - 1].upper() != 'P') and (y == 0 or normalized_map[y - 1][x].upper() != 'P'):
                if x + 1 < width and y + 1 < height:
                    portal_map[y][x] = 'P'
                    portal_map[y][x + 1] = 'P'
                    portal_map[y + 1][x] = 'P'
                    portal_map[y + 1][x + 1] = 'P'
    normalized_map = [''.join(row) for row in portal_map]

    with open(file_path, "wb") as f:
        f.write(struct.pack("<HHHH", width, height, start_x, start_y))
        def encode_tile(c):
            if c.isalpha():
                c = c.upper()
            return char_to_id.get(c, 0)
        f.write(bytes(encode_tile(c) for row in normalized_map for c in row))
    print(f"Created {filename} ({width}x{height})")


 
def create_all_levels():
    tutorial_map = [
        ".############",
        "...#.........",
        "...#..PP####.",
        "...#..PP#.X.#",
        ".#...#......#",
        ".##..########"
    ]
    write_level("tutorial.dat", tutorial_map, 2, 2)

    level1_map = [
        "########..#PP.....#",
        "#......#..#PP.....#",
        "#......#..###..####",
        "#......#..#.#......",
        ".........###.####PP",
        "#....#####PP.#...PP",
        "#..#......PP.#.X.##",
        "#..####......######",
        "#.......###........"
    ]
    write_level("level1.dat", level1_map, 2, 2)

    level2_map = [
        "##########################",
        "#......#.................#",
        "#..#...#...######..###...#",
        "#..#.......#.........#...#",
        "#..#####...##PP....X.#...#",
        "#......#...##PP......#...#",
        "####...#...###########...#",
        "#......#...#.............#",
        "#.######.###.#############",
        "#.#........#.#...........#",
        "#.#.######.###.#######...#",
        "#.#.#......#.#.......#...#",
        "#.#.#...PP##.#######.#...#",
        "#.#.####PP##.......#.#...#",
        "#.#................#.....#",
        "##########################"
    ]
    write_level("level2.dat", level2_map, 2, 2)
    
    level3_map = [
        "##############################",
        "#.......#................X...#",
        "#..#..#.#.#######.####...###.#",
        "#..#..#...#.....#.#........#.#",
        "#..####.###.###.#.####PP...#.#",
        "#.....#...#...#.#.####PP...#.#",
        "#####.###.###.#.#.#.######.#.#",
        "#.......#.....#.#.#.#.##.#.#.#",
        "#.#############.#.#.#.##.#.#.#",
        "#.#.............#.#.#....#.#.#",
        "#.#.#############.#.######.#.#",
        "#.#.#.........#####........#.#",
        "#.#.#.#############.########.#",
        "#.#.#.#.....#..######........#",
        "#.#.#.#.###.#.#######.########",
        "#.#.#...#.#.#..######........#",
        "#.#.#####.#.#######.########.#",
        "#.#.......#.......####PP#..#.#",
        "#.###############.####PP#..#.#",
        "#..........................#.#",
        "##############################"
    ]
    write_level("level3.dat", level3_map, 2, 2)


if __name__ == "__main__":
    create_all_levels()