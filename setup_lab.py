import os
import argparse
from helper import OscilloscopeDataCopier


parser = argparse.ArgumentParser(prog="Lab Setup",
                                 description="Setup a lab directory for the report")
parser.add_argument("lab_number", metavar='N', type=int, help="the number of the lab to setup")
parser.add_argument("-n", '--num-exercises', type=int, help="the number of exercises in the lab", default=0)
parser.add_argument("-g", "--generate-notebooks", action='store_true', help="generate starter jupyter notebooks")
parser.add_argument("-v", "--verbose", action='store_true', help="print info of the setup")
parser.add_argument("-d", '--drive-name', default='ECE65-DATA',
                    help="copy data from the flash drive with provided name")
parser.add_argument("-c", action="store_true", help="copy the data from the flash drive to a directory only")
parser.add_argument("-p", "--prelab-only", action="store_true", help="don't copy anything from a flash drive")
parser.add_argument("-sn", "--student-names", nargs="+", help="student name(s) to generate on the jupyter notebooks")
parser.add_argument("-si", "--student-ids", nargs="+", help="student id(s) to generate on the jupyter notebook")

args = parser.parse_args()

lab_number = args.lab_number
num_exercises = args.num_exercises
gen_notebooks = args.generate_notebooks
verbose = args.verbose
drive_name = args.drive_name
copy_only = args.c
prelab_only = args.prelab_only

if gen_notebooks:
    student_names = args.student_names
    student_ids = args.student_ids
    if not student_names or not student_ids:
        parser.error("You need to provide at least one student name and student id when generating notebooks")

    if len(student_names) != len(student_ids):
        parser.error("There are a different number of student names and student ids")

if prelab_only and copy_only:
    parser.error("Can't copy and not copy data from the flash drive")

if copy_only:
    print("Copying data from oscilloscope...")
    OscilloscopeDataCopier(drive_name=drive_name).copy_scope_data(copy_only, verbose=verbose)
else:
    # Create the lab directory and subdirectories
    lab_name = f"Lab {lab_number}"
    lab_dir = os.path.join(os.getcwd(), lab_name)

    if not os.path.exists(lab_dir):
        if verbose:
            print(f"Creating lab directory: {lab_dir}")
        os.makedirs(lab_dir)
    elif verbose:
        print(f"Lab directory already found at: {lab_dir}")

    for dir_type in ['assets', 'prelab', 'scope']:
        dir_to_add = os.path.join(lab_dir, dir_type)
        if not os.path.exists(dir_to_add):
            if verbose:
                print(f"Creating '{dir_type}' in {lab_name}: {dir_to_add}")
            os.makedirs(dir_to_add)
        elif verbose:
            print(f"'{dir_type}' already found in {lab_name}: {dir_to_add}")

    if num_exercises > 0:
        for i in range(1, num_exercises + 1):
            dir_to_add = os.path.join(lab_dir, 'prelab', f'exp{i}')
            if not os.path.exists(dir_to_add):
                if verbose:
                    print(f"Creating 'exp{i}' in 'prelab' of {lab_name}: {dir_to_add}")
                os.makedirs(dir_to_add)
            elif verbose:
                print(f"'exp{i}' already found in 'prelab' of {lab_name}: {dir_to_add}")

    if not prelab_only:
        print("Copying data from oscilloscope...")
        OscilloscopeDataCopier(drive_name=drive_name) \
            .copy_scope_data(os.path.join(lab_dir, 'scope'), verbose=verbose)

    if gen_notebooks:
        import nbformat as nbf

        name_string = ""
        for idx, (n, i) in enumerate(zip(student_names, student_ids)):
            suffix = ""
            if idx == len(student_names) - 2:
                suffix = ", and "
            elif idx != len(student_names) - 1:
                suffix = ", "

            name_string += f"{n} ({i})" + suffix

        prelab = nbf.v4.new_notebook()
        prelab_cells = [
            nbf.v4.new_markdown_cell(
                f"# ECE 65 - Components and Circuits Lab\n"
                f"## PreLab {lab_number}:\n" +
                name_string
            ),
            nbf.v4.new_code_cell(
                f"import os\n"
                f"import numpy as np\n"
                f"from glob import glob\n"
                f"from ltspice import Ltspice\n"
                f"import matplotlib.pyplot as plt\n"
                f"from IPython.display import display, Markdown\n"
                f"\n"
                f"from helper import Exercise\n"
                f"\n"
                f"plt.style.use(\"seaborn\")"
            )
        ]
        if num_exercises > 0:
            for i in range(1, num_exercises + 1):
                prelab_cells.append(nbf.v4.new_markdown_cell(
                    f"# Experiment {i}\n"
                    f"***Description***\n"
                    f"### Circuits for Simulation:\n"
                    f"![](assets/e{i}p1.png) \n"
                ))
                prelab_cells.append(nbf.v4.new_code_cell(
                    f"class Exercise{i}(Exercise):\n"
                    f"    def __init__(self):\n"
                    f"        data_path = os.path.join(os.getcwd(), \"prelabs\", \"exp{i}\")\n"
                    f"        super().__init__([os.path.join(data_path, \"E{i}P1.raw\")])\n"
                    f"        \n"
                    f"if __name__ == '__main__':\n"
                    f"    e{i} = Exercise{i}()\n"
                ))
        prelab['cells'] = prelab_cells
        if verbose:
            print(f"Generated prelab{lab_number}.ipynb")
        nbf.write(prelab, os.path.join(lab_dir, f'prelab{lab_number}.ipynb'))

        main_lab = nbf.v4.new_notebook()
        experiment_titles = [f'### - [Experiment {i}](#experiment-{i}):\n' for i in range(1, num_exercises + 1)]
        main_lab_cells = [
            nbf.v4.new_markdown_cell(
                f"# ECE 65 – Components and Circuits Lab\n"
                f"## Lab Report {lab_number} - \n"
                f"\n" +
                name_string +
                f"\n\n"
                f"Professor Saharnaz Baghdadchi"
            ),
            nbf.v4.new_markdown_cell(
                f"# Table of Contents\n"
                f"## [Abstract](#abstract)\n"
                f"## Experimental Procedures and Results\n" +
                ''.join(experiment_titles) +
                f"## [Conclusion](#conclusion)\n"
            ),
            nbf.v4.new_markdown_cell(
                "# Abstract\n"
                "This lab is...\n"
            ),
            nbf.v4.new_code_cell(
                f"import os\n"
                f"import numpy as np\n"
                f"import matplotlib.pyplot as plt\n"
                f"from ipynb.fs.full import prelab{lab_number}\n"
                f"from helper import get_scope_data"
            )
        ]
        if num_exercises > 0:
            for i in range(1, num_exercises + 1):
                main_lab_cells.append(nbf.v4.new_markdown_cell(
                    f"# Experiment {i}\n"
                    f"***Description***\n\n"
                    f"## PreLab\n\n"
                    f"### Circuits for Simulation:\n"
                    f"![](assets/e{i}p1.png) \n\n"
                    f"### Simulation:\n\n"
                ))
                main_lab_cells.append(nbf.v4.new_code_cell(
                    f"prelab{lab_number}.Exercise{i}().part_1()\n"
                    f"plt.show()\n"
                ))
                main_lab_cells.append(nbf.v4.new_markdown_cell(
                    "## Lab Exercises:"
                ))
        main_lab_cells.append(nbf.v4.new_markdown_cell(
            "# Conclusion"
        ))
        main_lab['cells'] = main_lab_cells
        if verbose:
            print(f"Generated Lab Report {lab_number}.ipynb")
        if os.path.exists(os.path.join(lab_dir, f'Lab Report {lab_number}.ipynb')):
            os.remove(os.path.join(lab_dir, f'Lab Report {lab_number}.ipynb'))
        nbf.write(main_lab, os.path.join(lab_dir, f'Lab Report {lab_number}.ipynb'))
print("Done.")
