#!/usr/bin/env python
# coding: utf-8

# ## 2. Finding Spikes!

# ### Note

# This section primairly focuses using IPFX to analyze your patch clamp data. In particular focuses on analyzing current clamp data. However you may find success with other analysis packages such as [https://github.com/BlueBrain/BluePyEfe](https://github.com/BlueBrain/BluePyEfe)

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyabf
import ipfx
from IPython.display import display, HTML


# In[2]:


abf = pyabf.ABF("data/example1.abf") #this tells pyabf to load our data and store it in an abf object
abf.setSweep(7)


# ### Setting up our spike finder

# To begin with, we will import just the spike finder from IPFX.

# In[3]:


from ipfx.feature_extractor import SpikeFeatureExtractor


# Now we will create our SpikeFeatureExtractor. To do so, we will create a object similar to our ABF object. We can pass our settings to the object, that way we will not have to specify the settings repeatedly. More on this later

# In[4]:


spike_fe = SpikeFeatureExtractor(filter=0) #Set the filter to 0


# The above command intializes the spike feature extractor. Similar to the abf object, this has many attributes we can access.

# In[5]:


dir(spike_fe)[-10:]


# ### Getting the Spikes

# To begin, we will use the `spike.process` function to find our data. This function takes our Time, Response, and Command waveforms as input.

# In[6]:


spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC) #Processes that specific sweep from the ABF file


# This returns a pandas `dataframe` containing information for each spike detected. These dataframes are similar to excel spread sheets. Each row is a single spike, and each column is a feature of that spike (for example peak voltage). For more explicit definitions of the various columns I recommend checking out the [Allen Institutes Ephys Whitepaper](http://help.brain-map.org/display/celltypes/Documentation). We can take a peek:

# In[7]:


display(spikes)


# We can also visualize the detected spikes on a plot:

# In[8]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.55, 1.5)


# The [pandas dataframe](https://pandas.pydata.org/pandas-docs/stable/reference/frame.html) contains a number of useful functions for analysis. For example we can take the mean of a column

# In[9]:


mean_trough = spikes['fast_trough_v'].mean()
print(f"Found a mean trough of {mean_trough}")


# In addition we can save the dataframe for opening later:

# In[10]:


spikes.to_csv("out.csv") #Outputs the dataframe to a csv for opening in excel
#The "out.csv" specifies the file location/name


# ### Ensuring you captures the spikes

# The above example uses the default spike finding options. This is suitable for many applications. However, one may find that this over/under detects spikes in your data. Take for example, the spikes found in one of the latter sweeps:

# In[11]:


abf.setSweep(14)
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[12]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.55, 1.5)


# It still catches most of the spikes, however, it misses one or two spikes at the end of the train that you may want to pick up. To ensure we pick up these spikes, we can adjust a few parameters available to us. We can view the available options here:

# In[13]:


help(spike_fe)


#  First, we will take a look at the dv/dt threshold!

# ####  dv_cutoff: dV/dT threshold

# The dV/dT threshold is the primary method by which ipfx detects spikes. Putative spikes must pass this check prior to any other settings being applied. By default, ipfx looks for points at which the dV/dT crosses 20mV/mS (V/s) (based on the ephys whitepaper noted above). if we examine the dV/dt of our trace, we can see that the smaller spikes do not reach this threshold

# In[14]:


dV = np.diff(abf.sweepY) #take the difference of the adjacent points in mV
dT = np.diff(abf.sweepX * 1000) #take the difference of adjacent points in s * 1000 -> ms
dvdt = dV/dT #compute dvdt in mV/ms -> v/s
plt.plot(abf.sweepX[:-1], dvdt)
plt.xlim(0.55, 0.8)
plt.axhline(20, label='20mV/ms', c='r') #plot a horizontal line at 20mV/ms
plt.axhline(10, label='10mV/ms', c='g') #plot a horizontal line at 20mV/ms
plt.legend()


# However, it appears that setting a threshold of 10mV/ms should do the trick! Now we will reinitialize the spike finder with the new threshold

# In[15]:


spike_fe = SpikeFeatureExtractor(filter=0, dv_cutoff=10) #reintialize with a dv threshold of 10
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[16]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.55, 1.5)


# Its looking good! However, lets say we decided to exclude the final spike in the train, we can adjust some of the other parameters to do so. 

# #### max_interval: Time between threshold and peak

# Max interval defines the maximum length of time between the detected threshold and the detected peak. In many cases the default (5ms) should be fine. However, if you have slow or oddly shaped spikes, you may find adjusting this parameter useful. Take for example our threshold to peak time from our last sweep.

# In[17]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
final_spike = spikes['peak_t'].to_numpy()[-1] #Gets the time of the last peak
final_threshold = spikes['threshold_t'].to_numpy()[-1] #gets the last threshgold
time = final_spike - final_threshold
print(f"Threshold to peak time of {time*1000}ms")


# In[52]:


sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.plot(np.linspace(final_threshold, final_spike, 10), np.full(10, -20), label="threshold to peak")
plt.xlabel("Time (s)")
plt.legend()
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.72, 0.74)
plt.ylim(-30, 0)


# By specifying the threshold-to-peak time we can drop this spike

# In[53]:


spike_fe = SpikeFeatureExtractor(filter=0, dv_cutoff=10, max_interval=0.00164) #Note that the units are in seconds
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[54]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.55, 1.5)


# Note that while we dropped that final spike, we lost other spikes! To remedy this, we can try adjusting the minimum height instead!

# #### min_height: the minimum height between threshold and peak

# The min height parameter defines the cutoff for the minimum amount of voltage an action potential must swing upward. This is computed as the difference between the peak and threshold. Therefore we will want to enter an absolute (non-negative) value. AP's with a height below this value will be rejected. This value defaults of 2mV.

# In[55]:


spike_fe = SpikeFeatureExtractor(filter=0, dv_cutoff=10, min_height=5) #reintialize with a min height of 5
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[56]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.55, 1.5)


# We can see that we have successfully excluded the last spike. If we examine closer we can examine the heights of the action potentials

# In[57]:


spike_fe = SpikeFeatureExtractor(filter=0, dv_cutoff=10) #reintialize with a min height of 5
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[61]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
final_spike = spikes['peak_v'].to_numpy()[-1] #Gets the time of the last peak
final_threshold = spikes['threshold_v'].to_numpy()[-1] #gets the last threshgold
height = final_spike - final_threshold


# In[62]:


sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.plot(np.full(10, spike_times.to_numpy()[-1]),np.linspace(final_threshold, final_spike, 10), label="threshold to peak")
plt.xlabel("Time (s)")
plt.legend
plt.ylabel(abf.sweepLabelY) #
plt.xlim(0.72, 0.74)
plt.ylim(-30, 0)


# #### min_peak: the minimum absolute peak of the action potential

# Similar to the setting above, we can set the cutoff for the min peak of the action potential. However, this value is not calculated in reference to the threshold, instead, it is computed as the minimum the peak must reach (regardless of distance between peak and threshold). Therefore, its okay to use negative numbers for this setting. Action potentials with peaks that do not reach this level will be rejected. This value defaults to -30

# In[63]:


spike_fe = SpikeFeatureExtractor(filter=0, dv_cutoff=10, min_peak=-10) #reintialize with a min peak 10
spikes = spike_fe.process(abf.sweepX, abf.sweepY, abf.sweepC)


# In[65]:


#isolate the columns for plotting
spike_times = spikes['peak_t'] #This isolates the peak_t columm
spike_peak = spikes['peak_v'] #this isolates the peak_v column
sweepX = abf.sweepX
sweepY = abf.sweepY
sweepC = abf.sweepC
#Create a figure
plt.figure(1)
plt.plot(sweepX, sweepY)
plt.scatter(spike_times, spike_peak, c='r', marker='x') #Plots X's at the peak of the action potential
plt.xlabel("Time (s)")
plt.axhline(-10, label="min_peak threshold of -10")
plt.ylabel(abf.sweepLabelY) 
plt.xlim(0.55, 1.5)


# zooming a bit closer shows us that this threshold of -10 allows us to exclude the last spike but keep the others!

# ### Putting it all together: Find spikes across all sweeps

# So far we have just been analyzing a single sweep of our ABF file. However functionally
