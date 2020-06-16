# KiCad Symbol and Footprint Converters

## Use

### Symbol conversion script syntax

- Mark the bash ***symbol_converter.sh*** file as an excecutable (***chmod -x symbol_converter.sh***)
- Run the bash script with the following parameters:
  - Relative path to directory containing the .asy files to symbol_convert
  - Relative path to lib_LTspice2Kicad.py
  - **Note:** you can use the absolute path as well
- Example call: ***./symbol_converter.sh 'target directory' lib_LTspice2Kicad.py***

### Footprint conversion script syntax

- The same as symbol conversion but use footprint_converter.sh instead
  - Paths to folder containing .fpl files to convert and to FreePCB2Kicad<nolink></nolink>.py
- Example call: ***./footprint_converter.sh 'target directory' FreePCB2Kicad<nolink></nolink>.py***

### **Important: Add a \ before spaces in paths, otherwise it will break the argument at the first space and fail to find the proper directory**

### Output folder location

- Creates an **output** folder in the target directory containing files to convert
- For the symbol conversion this folder contains **.lib** files for each folder containing **.asy** files within the target directory
- For the footprint conversion this folder contains **.pretty** folders for each folder within the target directory. These .pretty folders in turn contain **.kicad_mod** files for each **.fpl** file within the original corresponding folder

## Notes

### Formats

#### LTspice .asy files

- Since LTspice is not open source **.asy** files don't have an accessable discription of the file format so testing and examination was used to decipher it. As they are human readable text files this was very doable. The largest differences between them are:
  - In the **.asy** files each line contains only one piece of information. This means that when defining a pin the name, number and location/orientation/size are all on different lines. In the KiCad **.lib** files this is not the case.
  - KiCad **.lib** files contain more than one symbol while **.asy** files contain only one. This means that when converting a single **.lib** file represents an entire folder of **.asy** files

#### KiCad .lib files

- KiCad may be open source but it's doccumentation isn't any better. I was working from sombody on the KiCad forums personal copy of a 6 year old pdf that's main link is broken. After much googling I found it posted [here](https://lists.launchpad.net/kicad-developers/msg43412.html).
- This pdf has a number of issues, including inconsistancies between the description of the file format and the example lines given.
  - An example of these issues is the text field
  - The field is described as follows:
  >**T** orientation posx posy dimension unit convert Text
  - An example of this from the documentation is given as:
  >T 0 -320 -10 100 0 0 1 VREF
  - At first glance this looks fine but if you count the number of fileds before the text itself is given you'll see there is an extra one in the example that isn't accounted for in the documentation
  - In addition, KiCad 5.1.x has three more required fields for text elements after the Text field that aren't doccumented in this pdf
- In order to deal with these issues the format created by the converter doesn't exactly match what's layed out in the doccumentation

### Hard coded values in the symbol converter

- A number of parameters have been hard coded. These include:
  - Symbol type (Normal/power), set to normal
  - Text size, set to 50
  - Weather or not to pins
  - Not showing pin numbers
  - Pin length, set to 0
  - Pin type, set to unspecified
  - And more
- The documentation for each KiCad field is included above the line that field is generated/outputed in so you can compare the field names to hard coded values and modify things as you wish

### Encoding

#### UTF-8 vs UTF-16-LE

- Most of the LTspice **.asy** files are saved in UTF-8 but for an unknown reason some are saved in UTF-16-LE. In order to ensure that the files parse correctly it's needed to check which one the file is encoded in
  - To do this all files are decoded in UTF-8 and the first word is checked to see if it's the expected value (**.asy** files should always start with "version"). If the first word isn't expected the file is reopened with UTF-16-LE instead.

### Missing fields

- While useful this converter isn't perfect. LTspice has a large number of ways of drawing symbols that look functionally identical but programmatically are not
  - Drawing a rectangle with 4 polylines vs using a rectangle object is an example of this
    - They look the same in LTspice but in KiCad they are not. The rectangle can be filled with a background color while the four polyline rectangle cannot
  - Another example of this is pin names and text
    - In LTspice you can put a text field with the pin name next to the pin without labeling the pin and it will look the same as if it was the pin name. In KiCad they are different objects and will be filled with a different color.
- The converter will convert files as they are programmatically defined, leading to some inconsistencies and unexpected results. To prevent this make sure that the LTspice files you pass in are consistent

### Ellipses

- In LTspice you can draw circles and arcs, as well as ellipses and elliptical arcs.
- KiCad is not capable of drawing either ellipses or elliptical arcs.
- in order to deal with this and properly convert both to KiCad all circles and arcs are approximated using a variable polyline
  - Smaller circles have fewer points on their line and larger have more, keeping the resolution the same
  - This is by far the most complex portion of the program
