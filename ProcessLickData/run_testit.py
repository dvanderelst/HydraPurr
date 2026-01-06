from library import data_reader
from library import plot_licks_bouts_water

data_reader.print_data_folders_table()
contents = data_reader.read_data_folder(0)
print(
    f"{contents.name}: "
    f"licks={contents.licks is not None}, "
    f"system_log={contents.system_log is not None}"
)
if contents.licks is not None:
    print("licks rows:", len(contents.licks))
if contents.system_log is not None:
    print("system log rows:", len(contents.system_log))

plot_licks_bouts_water(
    0,
    save_html=True,
    extra_html_path="/home/dieter/Dropbox/HabitTechnology/Prototype_of_Hydropurr/testing/data/Dec_31_25",
)
