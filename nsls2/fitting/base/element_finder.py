'''
Copyright (c) 2014, Brookhaven National Laboratory
All rights reserved.

# @author: Li Li (lili@bnl.gov)
# created on 08/20/2014

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the Brookhaven National Laboratory nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from __future__ import (absolute_import, division)
import six
import numpy as np

from nsls2.fitting.base.element import Element


def element_finder(incident_energy, fluor_energy, diff,
                   elem_list=None):
        """
        Find emission lines close to a given energy

        Parameters
        ----------
        incident_e : float
            incident energy in KeV
        fluor_energy : float
            energy value to search for
        diff : float
            difference compared to energy
        elem_list : list
            List of elements to search for. Element abbreviations can be
            any mix of upper and lower case, e.g., Hg, hG, hg, HG

        Returns
        -------
        dict
            elements and possible lines
        """

        result = {}
        if not elem_list:
            for i in np.arange(100):
                e = Element(i+1, incident_energy)
                if find_line(e, fluor_energy, diff) is None:
                    continue
                result.update(find_line(e, fluor_energy, diff))
        else:
            for item in elem_list:
                e = Element(item, incident_energy)
                if find_line(e, fluor_energy, diff) is None:
                    continue
                result.update(find_line(e, fluor_energy, diff))

        return result


def find_line(element, energy, diff):
    """
    Fine possible line from a given element

    Parameters
    ----------
    element : class instance
        instance of Element
    energy : float
        energy value to search for
    diff : float
        define search range (energy - diff, energy + diff)

    Returns
    -------
    dict or None
        elements with associated lines
    """
    mydict = {k: v for k, v in six.iteritems(element.emission_line)
              if abs(v - energy) < diff}
    if len(mydict) == 0:
        return
    else:
        newdict = {k: v for k, v in six.iteritems(mydict) if element.cs[k] > 0}
        if len(newdict) == 0:
            return
        else:
            return {element.name: newdict}
