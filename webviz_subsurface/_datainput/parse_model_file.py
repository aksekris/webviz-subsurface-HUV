import os
from pathlib import Path
from bs4 import BeautifulSoup


def extract_surface_names(basedir):
    model_file = os.path.join(basedir, "model_file.xml")
    with open(model_file, "r") as file:
        soup = BeautifulSoup(file, "xml")
    surface_wrappers = soup.find_all("surface")
    surface_names = []
    for element in surface_wrappers:
        name = element.find("name")
        surface_names.append(name.get_text())
    return surface_names


def extract_topofzone_names(basedir):
    model_file = os.path.join(basedir, "model_file.xml")
    with open(model_file, "r") as file:
        soup = BeautifulSoup(file, "xml")
    surface_wrappers = soup.find_all("surface")
    topofzone_names = []
    for element in surface_wrappers:
        name = element.find("top-of-zone")
        topofzone_names.append(name.get_text())
    return topofzone_names


def get_surface_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_files = [
        os.path.join(surface_dir, "d_" + s + ".rxb") for s in surface_names
    ]
    for path in surface_files:
        if not os.path.isfile(path):
            raise FileNotFoundError
    return surface_files


def get_surface_de_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_de_files = [
        os.path.join(surface_dir, "de_" + s + ".rxb") for s in surface_names
    ]
    for path in surface_de_files:
        if not os.path.isfile(path):
            return None
    return surface_de_files


def get_surface_dr_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_dr_files = [
        os.path.join(surface_dir, "dr_" + surface_name + ".rxb")
        for surface_name in surface_names
    ]
    for path in surface_dr_files:
        if not os.path.isfile(path):
            return None
    return surface_dr_files


def get_surface_dre_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_dre_files = [
        os.path.join(surface_dir, "dre_" + surface_name + ".rxb")
        for surface_name in surface_names
    ]
    for path in surface_dre_files:
        if not os.path.isfile(path):
            return None
    return surface_dre_files


def get_surface_dt_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_dt_files = [
        os.path.join(surface_dir, "dt_" + surface_name + ".rxb")
        for surface_name in surface_names
    ]
    for path in surface_dt_files:
        if not os.path.isfile(path):
            return None
    return surface_dt_files


def get_surface_dte_files(basedir):
    surface_names = extract_surface_names(basedir)
    surface_dir = os.path.join(basedir, "output", "surfaces")
    surface_dte_files = [
        os.path.join(surface_dir, "dte_" + surface_name + ".rxb")
        for surface_name in surface_names
    ]
    for path in surface_dte_files:
        if not os.path.isfile(path):
            return None
    return surface_dte_files


def get_well_files(basedir):
    well_dir = os.path.join(basedir, "input", "welldata")
    well_files = []
    for file in os.listdir(well_dir):
        if Path(file).suffix == ".txt":
            well_files.append(os.path.join(well_dir, file))
    well_files.sort()
    return well_files


def get_target_points(basedir):
    return os.path.join(basedir, "output", "log_files", "targetpoints.csv")


def get_well_points(basedir):
    return os.path.join(basedir, "output", "log_files", "wellpoints.csv")


def get_zonelog_name(basedir):
    model_file = os.path.join(basedir, "model_file.xml")
    with open(model_file, "r") as file:
        soup = BeautifulSoup(file, "xml")
    zonelog_wrapper = soup.find("zone-log-name")
    return zonelog_wrapper.get_text()


def get_zonation_status(basedir):
    return os.path.join(basedir, "output", "log_files", "zonation_status.csv")
