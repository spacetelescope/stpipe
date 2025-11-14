.. _datamodels:

DataModels
==========

Although this package is primarily focused on data pipelines
some expectations are formalized for the data structures processed
with these pipelines. `~stpipe.Step` and `~stpipe.Pipeline` both
work best when processing classes that conform to `~stpipe.datamodel.AbstractDataModel`.
Data pipelines should implement a class that conforms to the abstract class
and any additional constraints documented in `~stpipe.datamodel.AbstractDataModel`.
