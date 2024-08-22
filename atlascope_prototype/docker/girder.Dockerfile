FROM girder/girder

WORKDIR /girder

RUN git clone https://github.com/DigitalSlideArchive/large-image-utilities.git

RUN pip install large-image[common] --find-links https://girder.github.io/large_image_wheels

RUN pip install girder-large-image-annotation

RUN girder build
