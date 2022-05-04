import os
import shutil
from glob import glob
from numpy import genfromtxt, ndarray
import matplotlib.pyplot as plt
from ltspice import Ltspice
from typing import Tuple, List, Union


def get_scope_data(filename: str) -> Tuple[ndarray, ndarray]:
    """
    Grabs and parses CSV output from an oscilloscope waveform sample. This function is adapted specifically to parse
    the data from a Tektronix TDS 1012C-EDU oscilloscope, in which the saved data is in format:
        SETTING, SETTING_VALUE, EMPTY, TIME, VOLTAGE
    This function is only interested in grabbing the 3rd and 4th column, the time and voltage column.

    Args:
        filename: string to the CSV file with the oscilloscope sample data

    Returns: (time, voltage)
        time: ndarray containing the time values from the oscilloscope sample
        voltage: ndarray containing the voltage values from the oscilloscope sample

    """
    arr = genfromtxt(filename, delimiter=",")
    return arr[:, 3], arr[:, 4]


def plot_vi_vo(vi: ndarray, vo: ndarray, time: ndarray, save: str = None) -> plt:
    """
    Quickly plots input and output voltage waveforms.
    Args:
        vi: ndarray with input voltage data
        vo: ndarray with output voltage data
        time: ndarray with time data
        save: str of the location to save the file to

    Returns: the plot if it isn't saved

    """
    plt.title("$v_i$ and $v_o$")
    plt.plot(time, vi)
    plt.plot(time, vo)
    plt.legend(["$v_i$", "$v_o$"])
    plt.xlabel("time (s)")
    plt.ylabel("voltage (V)")
    if save:
        plt.savefig(save)
        plt.close()
    else:
        return plt


class Exercise:
    """
    Base class for pre-lab simulations. Provides a quick and easy way to parse LTSpice data for our lab report use.
    """
    def __init__(self, filepath: Union[str, List[str]]) -> None:
        """
        Instantiate an object with as many LTSpice readers as needed.
        Args:
            filepath: a single str or list of strings with filepaths to LTSpices' ".RAW" files
        """
        if isinstance(filepath, str):
            self.sim: Ltspice = Ltspice(file_path=filepath)
            self.sim.parse()
            self.size = -1
        else:
            self.sim: List[Ltspice] = [Ltspice(file_path=f) for f in filepath]
            for sim in self.sim:
                sim.parse()
            self.size = len(self.sim)

    def get_plot(self):
        """
        Not implemented method that would allow Exercises to quickly plot some values
        """
        pass


class OscilloscopeDataCopier:
    """
    Class to quickly copy and parse and ready the data for use from an external flash drive that has folders labeled
    like:
        E<N>P<M>
    where <N> is the exercise number this plot corresponds to and <M> is the plot number for this exercise

    The Tektronix TDS 1012C-EDU stores its sample like:
        ALL0000/
        ├── F0000CH1.CSV
        ├── F0000CH2.CSV
        ├── F0000TEK.JPG
        └── F0000TEK.SET
    It is important that the user renames the parent directory to E<N>P<M> as otherwise the script will not copy it over
    """
    class File:
        """
        File child class helper to save the file
        """
        def __init__(self, location: str):
            """
            Creates a File object based on the given location
            Args:
                location: location of where this file is
            Raises:
                FileNotFoundError: if the location of the file doesn't exist
            """
            if os.path.exists(location):
                self.location = location
                self.name = os.path.basename(self.location)
            else:
                raise FileNotFoundError(location + " not found!")

        def save(self, destination: str, verbose: bool = True, softrun: bool = False):
            """
            Saves the file to a destination
            Args:
                destination: where to save the file to
                verbose: whether to print out the moving dialog
                softrun: whether to run the code without actually moving files
            """
            if not os.path.exists(destination):
                raise FileNotFoundError(destination + " not found!")

            if verbose or softrun:
                print(f"\t{self.location} -> {os.path.join(destination, self.name)}")

            if not softrun:
                shutil.copy(self.location, os.path.join(destination, self.name))

        def __str__(self) -> str:
            """
            Returns:
                str: location of the string
            """
            return str(self.location)

    class CSVFile(File):
        """
        CSV file, which is responsible for renaming itself before saving
        """
        def __init__(self, location: str, rename: bool = True):
            """
            Creates and renames a CSV file before saving. The CSV file is renamed to this format:
                e<N>P<M>.ch<O>.csv
            where <N> & <M> are inherited from the parent directory of where the original file is stored, and <O> is the
            channel of this specific file
            Args:
                location: location of this file
                rename: control renaming of the file
            """
            super().__init__(location)
            if rename:
                self.name = (str(self.location).split("/")[-2] + "." + self.name[-7:]).lower()

    class JPGFile(File):
        """
        JPEG file, which is a redundancy in case our data is corrupted, we can simply embed the image. It is renamed
        similarly to a CSV file
        """
        def __init__(self, location: str):
            """
            Creates and renames a JPG file before saving. The JPEG file is renamed to this format:
                e<N>p<M>.jpg
            where <N> & <M> are inherited from the parent directory of where the original file is stored.
            Args:
                location: location of this file
            """
            super().__init__(location)
            self.name = str(self.location).split("/")[-2].lower() + ".jpg"

    def __init__(self, drive_name: str = "ECE65-DATA"):
        """
        Creates an OscilloscopeDataCopier object. This copier is meant for macOS, and will look for
        drives under /Volumes/
        Args:
            drive_name: name of the drive to search from
        Raises:
            FileNotFoundError: if there isn't a drive name like the one given
        """
        self.drive_location = os.path.join("/Volumes", drive_name)
        if not os.path.exists(self.drive_location):
            raise FileNotFoundError("There is no drive named " + drive_name)

        self.exercise_parts = glob(os.path.join(self.drive_location, "E*P*"))
        if not len(self.exercise_parts):
            print("[WARN]: No folders matching E<N>P<M>!")

    def copy_scope_data(self, destination: str,
                        create_folders: bool = False,
                        rename_csv: bool = True,
                        save_jpg: bool = True,
                        verbose: bool = True,
                        softrun: bool = False):
        """
        Copies the oscilloscope data from the drive and pastes it into a destination directory
        Args:
            destination: destination to save the file in
            create_folders: create folders similar to how the data was saved
            rename_csv: rename csv files
            save_jpg: save jpg files
            verbose: print information of what's happening
            softrun: don't move any files and ensure everything works
        Raises:
            FileNotFoundError: if destination doesn't exist
        """
        if not os.path.exists(destination):
            raise FileNotFoundError()

        if save_jpg:
            if verbose:
                print("\tSaving JPG Files...")
            to_save_path = os.path.join(destination, "jpgs")
            if not os.path.exists(to_save_path):
                os.makedirs(to_save_path)
            for exercise_part in self.exercise_parts:
                self.JPGFile(glob(os.path.join(exercise_part, "*.JPG"))[0]) \
                    .save(to_save_path, verbose=verbose, softrun=softrun)
            if softrun:
                os.rmdir(to_save_path)
            print()

        if verbose:
            print("\tSaving CSV Files...")
        for exercise_part in self.exercise_parts:
            to_save_path = os.path.join(destination, os.path.basename(exercise_part)) if create_folders else destination
            if create_folders and not os.path.exists(to_save_path):
                os.makedirs(to_save_path)
            for csv_file in glob(os.path.join(exercise_part, "*.CSV")):
                self.CSVFile(csv_file, rename_csv) \
                    .save(to_save_path, verbose=verbose, softrun=softrun)
            if softrun and create_folders:
                os.rmdir(to_save_path)


if __name__ == '__main__':
    pass
