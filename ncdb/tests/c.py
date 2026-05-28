
def create_test_file(path, value):

    nc = Dataset(path, "w")

    nc.createDimension("nlocs", 1)

    obs = nc.createGroup("ObsValue")
    meta = nc.createGroup("MetaData")

    temp = obs.createVariable(
        "seaSurfaceTemperature",
        "f4",
        ("nlocs",)
    )

    lat = meta.createVariable(
        "latitude",
        "f4",
        ("nlocs",)
    )

    lon = meta.createVariable(
        "longitude",
        "f4",
        ("nlocs",)
    )

    temp[:] = np.array([value])

    lat[:] = np.array([10.0])

    lon[:] = np.array([100.0])

    nc.close()

