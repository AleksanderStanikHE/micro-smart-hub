from setuptools import setup, find_packages

setup(
    name="micro-smart-hub",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flake8',
        'numpy',
        'requests',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            # 'console_script_name = micro_smart_hub.module:function',
        ],
    },
    author="Aleksander Stanik (Olek)",
    author_email="aleksander.stanik@hammerheadsengineers.com",
    description="A small smart hub building blocks package",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/AleksanderStanikHE/micro-smart-hub.git",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
