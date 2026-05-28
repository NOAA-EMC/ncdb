
def create_test_file(path):

    nc = Dataset(path, "w")

    #
    # dimensions
    #
    nc.createDimension("nlocs", 3)

    #
    # groups
    #
    obs = nc.createGroup("ObsValue")
    meta = nc.createGroup("MetaData")

    #
    # variables
    #
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

    #
    # data
    #
    temp[:] = np.array([300.0, 301.0, 302.0])

    lat[:] = np.array([10.0, 20.0, 30.0])

    lon[:] = np.array([100.0, 110.0, 120.0])

    nc.close()

