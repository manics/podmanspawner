import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="podmanclispawner",
    author="Simon Li, Niklas Netter",
    description="PodmanCLISpawner for JupyterHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    use_scm_version=True,
    url="https://github.com/manics/podmanspawner",
    packages=setuptools.find_packages(),
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    project_urls={
        "Documentation": "https://jupyterhub.readthedocs.io",
        "Source": "https://github.com/manics/podmanspawner",
        "Tracker": "https://github.com/manics/podmanspawner/issues",
    },
    platforms="Linux",
    python_requires=">=3.6",
    setup_requires=["setuptools_scm"],
    install_requires=["jupyterhub", "traitlets>=4.3.2"],
    entry_points={
        "jupyterhub.spawners": [
            "podmancli = podmanclispawner:PodmanCLISpawner",
        ],
    },
)
