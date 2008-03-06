from pychart import *
#theme.get_options()
theme.output_format = "png"
#theme.output_format = "x11"
theme.reinitialize()
import sys

def stat( data ):
    ar = area.T( size=(500,500),
      x_axis= axis.X(label="Taxa number"),
      y_axis = axis.Y(label="Trees number")
    )
    ar.add_plot(bar_plot.T(data=data, fill_style = None))
    a = ar.draw()

a = eval(sys.argv[1])
stat( a )
