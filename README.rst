ulog_explorer
================


Postprocessing tool for uLog files inspired by `pyFlightAnalysis <https://github.com/Marxlp/pyFlightAnalysis>`__, `flight_review <https://github.com/PX4/flight_review/>`__ and `matulog <https://github.com/CarlOlsson/matulog>`__.

Under development, to try it out, clone the repo and run python3 ulog_analysis.py.

Instructions

* Right click on the plot to access most functionality
* Add your uLog file as an argument when launching ulog_explorer
* Press C to clear the plot
* Press V to auto range the visible range of the graph
* Press B to display bold curves
* Press M to display a marker at every data sample
* Press O to open a new logfile, directory starts at main logfile
* Press U to open a secondary logfile in a split screen environment. Directory starts at secondary logfile if possible
* Press K to link the x and y axes of the plots
* Press Q to display a 2D trajectory analysis
* Press D to display a marker line and the position on the trajectory if enabled
* Press Right/Left Arrow to move the marker line
* Press I to display vertical lines at start and stop of VTOL transitions
* Press L to display the graph lagend
* Press A to display a ROI and N to print the mean and diff to the command line
* Press R to rescale all curves to [0,1]
* Press F to move focus to the topic search box
* Press Down Arrow, Enter or Tab to move focus from topic search box to the topic tree

Additional notes

* A triangle is displayed on the curve if a logged value is a nan
* If the topic field ends with "flags" the individual bits will be displayed on the marker line
* When right clicking on the graph and selecting open main/secondary logfile the directory starts at the selected logfile in the graph that was pressed