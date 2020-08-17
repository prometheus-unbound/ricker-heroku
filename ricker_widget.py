''' Example used to interactively show how the indexing works
for the power spectrum for a wavelet - here we just use a Ricker.

The code demonstrate that indexing and bounds of the frequency
vector depend only on the sample rate and length of the wavelet.

Code adapted from a Bokeh script found at:
https://github.com/bokeh/bokeh/blob/master/examples/app/sliders.py

Use the ``bokeh serve`` command to run the example by executing:

    bokeh serve bokeh_ricker_power.py

at your command prompt. Then navigate to the URL

    http://localhost:5006/bokeh_ricker_power

in your browser.

Evan Delaney (evde) @ Equinor - 19 August 2020

'''

### import libraries
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput
from bokeh.plotting import figure
from bokeh.models import Range1d

# for table
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.io import output_file, show
from bokeh.models import HoverTool


### define necessary functions
# function to create a Ricker wavelet
def createRicker(fpeak=20,scalar=1,signalLength=256,sampleRate=4):
    ''' Creates a symmetric Ricker wavelet in the time domain
        whose length has a odd number of samples such that that
        for a zero phase case, the peak is centered at t=0.
        
        Inputs: 
            fpeak - dominant frequency for Ricker wavelet in Hz
            scalar - amplitude at the dominant frequency
            signalLength - the length of the wavelet in ms
            sampleRate - the sample rate of the wavelet in ms

        Returns: 
            ricker - amplitudes for Ricker wavelet
            t - time indices for Ricker wavelet

    '''

    # indexLimit defines number of elements above for time vector above and below t=0
    indexLimit = int(signalLength / 2 / sampleRate) 
    t = np.arange(-indexLimit * sampleRate, (indexLimit+1) * sampleRate, sampleRate) # now make odd length vector
    omega = 2 * np.pi * fpeak
    ricker = scalar * (1. - 0.5 * omega**2 * (t/1000)**2) * np.exp(-0.25 * omega**2 * (t/1000)**2)

    return ricker, t


# function to compute a wavelet's Power Spectrum
def computePowerSpectrum(wavelet,timeVector):
    ''' Takes a wavelet in time and its associated time vector, 
        fourier transforms it to one-sided frequency domain, 
        computes its power spectrum and associated frequency bins.

        -Signal must contain an odd number of samples.

        -Wavelets are expected to have Hermitic transforms.

        -Uses a scale factor in Fourier transform that honors energy conservation.

        Inputs:
        wavelet - the wavelet's amplitude
        timeVector - the associated time vector whose length is same as wavelet's

        Returns: 
            power - power spectrum
            powerNormdB - normalized power spectrum in dB
            freq - frequency indices

    '''

    if len(wavelet) % 2 == 0:
        raise ValueError('Given signal contains an even number of elements.')

    if len(wavelet) != len(timeVector):
        raise ValueError('The wavelet and time vector do not have same number of elements')


    # first derive some information from timeVector
    signalLength = timeVector[-1] - timeVector[0]
    sampleRate = timeVector[1] - timeVector[0]

    # compute Fourier transform that preserves energy conservation
    wavelet_fft = np.fft.fft(wavelet,norm='ortho')

    # Next, compute the power spectrum
    power = np.abs(wavelet_fft)**2

    # Transform is Hermitian, so convert to one-sided power spectrum
    indexLimit = int(signalLength / 2 / sampleRate)
    power = np.append(power[0],2*power[1:indexLimit+1])

    # now compute one-sided normalized power spectrum in dB
    powerNormdB = 10 * np.log10(power/np.max(power))

    # now determine frequency bins - this formula is for vectors whose length is odd
    scaleFactor = 1 / ((sampleRate/1000) * (2*indexLimit+1))
    freq = scaleFactor * np.arange(0,indexLimit+1)

    return power, powerNormdB, freq


### create wavelet and power spectrum:
# initiate variables
fpeak=20
scalar=1
signalLength=256
sampleRate=4

# create Ricker wavelet
ricker, t = createRicker(fpeak,scalar,signalLength,sampleRate)

# compute Power Spectrum for that wavelet, let us just get normalized one
_, powerNormdB, freq = computePowerSpectrum(ricker,t)


### set up front-end
# for plotting, we need two sources
source = ColumnDataSource(data=dict(x=t, y=ricker))
source2 = ColumnDataSource(data=dict(x=freq, y=powerNormdB))

## set up plots - plot1
# define axes for wavelet plot in time domain:
plot1_xlim = source.data['x'].max() 
plot1_ylim = 1.1 * abs(source.data['y']).max()

# initiate plot1
plot1 = figure(plot_height=400, plot_width=400, title="Wavelet in time-domain",
              tools="crosshair,pan,reset,save,wheel_zoom",
              x_range=[-1*plot1_xlim, plot1_xlim],
              y_range=[-1*plot1_ylim, plot1_ylim])

plot1.xaxis.axis_label = 'time (ms)'
plot1.yaxis.axis_label = 'amplitude'

# set up hover functionality so we can see indexed values
plot1_hover = HoverTool(tooltips=[
    ("index", "$index"),
    ("(t (ms),amp)", "(@x, @y)"),
    ],
    mode='vline'
)

plot1_hover.point_policy='snap_to_data'
#plot1_hover.line_policy='none'

plot1.add_tools(plot1_hover)

# and finally plot line
plot1.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


## set up plots - plot2
# define axes for Power Spectrum:
plot2_xlim = source2.data['x'].max()
plot2_ymin = -62.5
plot2_ymax = 2.5 

# initiate plot1
plot2 = figure(plot_height=400, plot_width=400, title="Power Spectrum",
              tools="crosshair,pan,reset,save,wheel_zoom",
              x_range=[0, plot2_xlim],
              y_range=[plot2_ymin, plot2_ymax])

plot2.xaxis.axis_label = 'frequency (Hz)'
plot2.yaxis.axis_label = 'normalized dB (1/Hz)'


# set up hover functionality so we can see indexed values
plot2_hover = HoverTool(tooltips=[
    ("index", "$index"),
    ("(freq (Hz), power (dB))", "(@x, @y)"),
    ],
    mode='vline'
)

plot2_hover.point_policy='snap_to_data'
#plot2_hover.line_policy='none'

plot2.add_tools(plot2_hover)

# and finally plot line
plot2.line('x', 'y', source=source2, line_width=3, line_alpha=0.6)


## let us also define some tables
# for wavelet in time domain
columns1 = [
        TableColumn(field="x", title="Time (ms)"),
        TableColumn(field="y", title="Amplitude"),
    ]
data_table1 = DataTable(source=source, columns=columns1, width=400, height=400)

# for power spectrum
columns2 = [
        TableColumn(field="x", title="Frequency (Hz)"),
        TableColumn(field="y", title="Normalized dB (1/Hz)"),
    ]
data_table2 = DataTable(source=source2, columns=columns2, width=400, height=400)


## set up widgets
#text = TextInput(title="title", value='My Ricker Wavelet')
fpeak_widget = Slider(title="Dominant Frequency (Hz)", value=20, start=1, end=100, step=1)
scalar_widget = Slider(title="Maximum Amplitude", value=1, start=-10, end=10, step=1)
signalLength_widget = Slider(title="Wavelet Length (ms)", value=256, start=1, end=2096, step=1)
sampleRate_widget = Slider(title="Sample Rate (ms)", value=4, start=1, end=25, step=0.5)

# Set up callbacks
#def update_title(attrname, old, new):
#    plot1.title.text = text.value

#text.on_change('value', update_title)

def update_data(attrname, old, new):
    # Get the current slider values
    fpeak_update = fpeak_widget.value
    scalar_update = scalar_widget.value
    signalLength_update = signalLength_widget.value
    sampleRate_update = sampleRate_widget.value

    # Generate the new data and curves curve
    ricker, t = createRicker(fpeak_update,scalar_update,signalLength_update,sampleRate_update)
    _, powerNormdB, freq = computePowerSpectrum(ricker,t)

    source.data = dict(x=t, y=ricker)
    source2.data = dict(x=freq, y=powerNormdB)

    plot1.x_range.start = source.data['x'].min()
    plot1.x_range.end = source.data['x'].max()
    #print(-1.1 * abs(source.data['y']).max())
    #print(-1.1 * abs(source.data['y']).max())
    plot1.y_range.start = -1.1 * abs(source.data['y']).max()
    plot1.y_range.end = 1.1 * abs(source.data['y']).max()
    plot2.x_range.end = source2.data['x'].max()

    plot1.title.text = "Wavelet - actual length: " + str(plot1.x_range.end-plot1.x_range.start) + " ms; dt: " + str(round(source.data['x'][1]-source.data['x'][0],1)) + " ms" 
    plot2.title.text = "Power Spectrum - max freq: " + str(round(plot2.x_range.end,2)) + " Hz; df: " + str(round(source2.data['x'][1]-source2.data['x'][0],2)) + " Hz" 

for w in [fpeak_widget, scalar_widget, signalLength_widget, sampleRate_widget]:
    w.on_change('value', update_data)

## setup layouts
# borrowed this nested row setup from:
# https://github.com/bokeh/bokeh/blob/master/examples/app/stocks/main.py

inputs = column(fpeak_widget, scalar_widget, signalLength_widget, sampleRate_widget)
#main_row = row(inputs,plot1)
#spectrum_column = column(plot2, data_table)
#layout = row(main_row, spectrum_column)

wavelet_column =  column(plot1, data_table1)
spectrum_column = column(plot2, data_table2)
layout = row(inputs, wavelet_column, spectrum_column)

curdoc().add_root(layout)
curdoc().title = "Ricker Gone Wild"	