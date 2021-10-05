import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gym-bb",  # Replace with your own username
    version="1.1.0",
    author="Dawson Horvath",
    author_email="horvath.dawson@gmail.com",
    description="gym-ignition environments for baesian balacning development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Baesian-Balancer/gym-bb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
          'numpy',
          'SIMP@git+https://github.com/Baesian-Balancer/SIMP.git@v1.0.0',
          'gym-ignition==v1.3.0',
    ],
    python_requires='>=3.8',
)
