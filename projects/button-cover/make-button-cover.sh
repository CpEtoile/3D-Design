python src/generate_rectangle_from.py --output part1_1.stl --outer-width 85 --outer-length 60 --inner-width 62 --inner-length 55 --height 3
python src/generate_rectangle_from.py --output part1_2.stl --outer-width 65 --outer-length 58 --inner-width 62 --inner-length 55 --height 20
python src/merge_stl.py --base part1_1.stl --attach part1_2.stl --output part1.stl --axis z --overlap 2

python src/generate_rectangle_from.py --output part2_1.stl --outer-width 67 --outer-length 60 --inner-width 65 --inner-length 58 --height 60
python src/generate_rectangle_from.py --output part2_2.stl --outer-width 67 --outer-length 60 --inner-width 0 --inner-length 0 --height 2
python src/merge_stl.py --base part2_1.stl --attach part2_2.stl --output part2.stl --axis z --overlap 2

