![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# Marco's Pulse Density Modulators

This TinyTapeout submission is a collection of Pulse Density Modulators (PDM).

<img width="684" alt="スクリーンショット 2022-12-26 10 49 35" src="https://camo.githubusercontent.com/63361edbc8bdb75bafb490cf3447c9942f3866d076e79bdc213507299c99ecbf/68747470733a2f2f62617435322e6769746875622e696f2f747430332d6464706d2d70776d2f6764735f72656e6465722e706e67">

# Description
This project implements three different architectures of Pulse Density Modulators (PDM), to compare performances and 
      implementation complexity of the different schemes.
      
      PDM modulators are of particular interest because exploiting oversampling, they allow to implement 
      Digital-to-Analog-Conversion (DAC) schemes with an equivalent resolution of multiple bits, based on 
      a single-bit digital output, by means of a straightforward analogue low-pass filter.      

      The PDM modulators implemented in this project are the following:
        1) Pulse Width Moulation (PWM)
        2) Dyadic Digital Pulse Modulation (DDPM)
        3) Sigma-Delta (SD)

## Sine Modulation

<img src="https://github.com/bat52/tt03-ddpm-pwm/blob/main/src/octave/timedomain.png">
<img src="https://github.com/bat52/tt03-ddpm-pwm/blob/main/src/octave/freqdomain.png">
<img src="https://github.com/bat52/tt03-ddpm-pwm/blob/main/src/octave/sd.png">

## Links

- [3D Viewer](https://gds-viewer.tinytapeout.com/?model=https://bat52.github.io/tt03-ddpm-pwm/tinytapeout.gds.gltf)

## References:

- [[1] "Standard Cell-Based Ultra-Compact DACs in 40nm CMOS", Aiello et al.](https://www.researchgate.net/publication/335513725_Standard_Cell-Based_Ultra-Compact_DACs_in_40nm_CMOS)
- [[2] "All-Digital High Resolution D/A Conversion by Dyadic Digital Pulse Modulation", Crovetti](https://www.researchgate.net/publication/309012492_All-Digital_High_Resolution_DA_Conversion_by_Dyadic_Digital_Pulse_Modulation/citations)
- [[3] "Spectral characteristics of DDPM streams and their application to all‐digital amplitude modulation", Crovetti](https://www.researchgate.net/publication/348654600_Spectral_characteristics_of_DDPM_streams_and_their_application_to_all-digital_amplitude_modulation)

# What is Tiny Tapeout?

TinyTapeout is an educational project that aims to make it easier and cheaper than ever to get your digital designs manufactured on a real chip!

Go to https://tinytapeout.com for instructions!

## How to change the Wokwi project

Edit the [info.yaml](info.yaml) and change the wokwi_id to match your project.

## How to enable the GitHub actions to build the ASIC files

Please see the instructions for:

* [Enabling GitHub Actions](https://tinytapeout.com/faq/#when-i-commit-my-change-the-gds-action-isnt-running)
* [Enabling GitHub Pages](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)

## How does it work?

When you edit the info.yaml to choose a different ID, the [GitHub Action](.github/workflows/gds.yaml) will fetch the digital netlist of your design from Wokwi.

After that, the action uses the open source ASIC tool called [OpenLane](https://www.zerotoasiccourse.com/terminology/openlane/) to build the files needed to fabricate an ASIC.

## Resources

* [FAQ](https://tinytapeout.com/faq/)
* [Digital design lessons](https://tinytapeout.com/digital_design/)
* [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
* [Join the community](https://discord.gg/rPK2nSjxy8)

## What next?

* Share your GDS on Twitter, tag it [#tinytapeout](https://twitter.com/hashtag/tinytapeout?src=hashtag_click) and [link me](https://twitter.com/matthewvenn)!
