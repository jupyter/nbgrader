A summary of changes to nbgrader.

## 0.7.x

<!-- <START NEW CHANGELOG ENTRY> -->

## 0.8.0a1

([Full Changelog](https://github.com/jupyter/nbgrader/compare/v0.8.0a0...86861f3ccdfa1c32a9a78c14e9fdaba1d7c913c1))

### Enhancements made

- Fix version error message [#1616](https://github.com/jupyter/nbgrader/pull/1616) ([@brichet](https://github.com/brichet))

### Maintenance and upkeep improvements

- Move the jupyter_releaser hooks from package.json to pyproject.toml [#1617](https://github.com/jupyter/nbgrader/pull/1617) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbgrader/graphs/contributors?from=2022-06-28&to=2022-07-04&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Abrichet+updated%3A2022-06-28..2022-07-04&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 0.8.0a0

([Full Changelog](https://github.com/jupyter/nbgrader/compare/v0.7.0...840e6abaa78f8f0764b805da5413e8f28abe90c0))

### Enhancements made

- Create assignment panel only open if a Notebook is visible on main area [#1606](https://github.com/jupyter/nbgrader/pull/1606) ([@brichet](https://github.com/brichet))
- Use jupyter css variable in labextension to manage colors with theme [#1603](https://github.com/jupyter/nbgrader/pull/1603) ([@brichet](https://github.com/brichet))
- Jupyterlab extensions [#1588](https://github.com/jupyter/nbgrader/pull/1588) ([@brichet](https://github.com/brichet))
- Jupyter server [#1586](https://github.com/jupyter/nbgrader/pull/1586) ([@brichet](https://github.com/brichet))

### Bugs fixed

- More informative error messages in ClearSolutions [#1607](https://github.com/jupyter/nbgrader/pull/1607) ([@jhamrick](https://github.com/jhamrick))
- Fix demos for JupyterHub 2.0 and JupyterLab [#1601](https://github.com/jupyter/nbgrader/pull/1601) ([@jhamrick](https://github.com/jhamrick))
- Fix mathjax in formgrade templates [#1598](https://github.com/jupyter/nbgrader/pull/1598) ([@brichet](https://github.com/brichet))
- Change default exchange path [#1592](https://github.com/jupyter/nbgrader/pull/1592) ([@jhamrick](https://github.com/jhamrick))
- Ensure html files aren't copied over from documentation [#1590](https://github.com/jupyter/nbgrader/pull/1590) ([@jhamrick](https://github.com/jhamrick))

### Maintenance and upkeep improvements

- Fix missing `.` in the JS version [#1614](https://github.com/jupyter/nbgrader/pull/1614) ([@jtpio](https://github.com/jtpio))
- Pins selenium version to 4.2 [#1611](https://github.com/jupyter/nbgrader/pull/1611) ([@brichet](https://github.com/brichet))
- Fix version bumping for pre-releases [#1610](https://github.com/jupyter/nbgrader/pull/1610) ([@jtpio](https://github.com/jtpio))
- Fix demos for JupyterHub 2.0 and JupyterLab [#1601](https://github.com/jupyter/nbgrader/pull/1601) ([@jhamrick](https://github.com/jhamrick))
- Don't depend on qtconsole [#1596](https://github.com/jupyter/nbgrader/pull/1596) ([@minrk](https://github.com/minrk))
- Fix readthedocs automatic build [#1587](https://github.com/jupyter/nbgrader/pull/1587) ([@brichet](https://github.com/brichet))

### Documentation improvements

- Add instruction to run playwright tests [#1602](https://github.com/jupyter/nbgrader/pull/1602) ([@brichet](https://github.com/brichet))
- Fix readthedocs automatic build [#1587](https://github.com/jupyter/nbgrader/pull/1587) ([@brichet](https://github.com/brichet))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/nbgrader/graphs/contributors?from=2022-05-07&to=2022-06-28&type=c))

[@brichet](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Abrichet+updated%3A2022-05-07..2022-06-28&type=Issues) | [@jhamrick](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Ajhamrick+updated%3A2022-05-07..2022-06-28&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Ajtpio+updated%3A2022-05-07..2022-06-28&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Aminrk+updated%3A2022-05-07..2022-06-28&type=Issues) | [@perllaghu](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Aperllaghu+updated%3A2022-05-07..2022-06-28&type=Issues) | [@rkdarst](https://github.com/search?q=repo%3Ajupyter%2Fnbgrader+involves%3Arkdarst+updated%3A2022-05-07..2022-06-28&type=Issues)

### 0.7.1

The following PRs were merged for the 0.7.1 milestone:

-   PR \#1607: More informative error messages in ClearSolutions
-   PR \#1598: Fix mathjax in formgrade templates
-   PR \#1593: Pin traitlets dependency for 0.7.x
-   PR \#1590: Ensure html files aren't copied over from documentation
-   PR \#1582: Trivial typo: "int the database"
-   PR \#1579: Only add extra\_template\_basedirs if it has not been set
-   PR \#1576: Revert "[converters/autograde] Fix autograded notebook permission"
-   PR \#1518: [converters/autograde] Fix autograded notebook permission

Thanks to the following users who submitted PRs or reported issues that were merged or fixed for the 0.7.1 release:

-   Anmol23oct
-   brichet
-   jhamrick
-   kno10
-   mhwasil
-   szazs89
-   tmetzl

### 0.7.0

The following PRs were merged for the 0.7.0 milestone:

-   PR \#1572: Fix a false positive test
-   PR \#1571: Add workflow to enforce GitHub labels
-   PR \#1569: Add Python 3.10 to CI pipeline
-   PR \#1568: Update markupsafe requirement from \<2.1.0 to \<### 2.2.0   PR \#1567: Upgrade nbconvert
-   PR \#1565: Bump pytest from 6.2.4 to ### 7.1.2   PR \#1564: Pin to [notebook\<7]{.title-ref} for now
-   PR \#1561: Add missing \'self\' argument to
    [late\_submission\_penalty]{.title-ref}
-   PR \#1559: Fix breaking tests due to changes in the newest Jinja2
    release
-   PR \#1558: Bump pytest-xdist from 2.4.0 to ### 2.5.0   PR \#1557: Update jupyter-client requirement from \<7 to \<8
-   PR \#1541: Update setup.py with dependency ranges
-   PR \#1539: Improve CI by running sphinx linkcheck
-   PR \#1519: Make generate solutions preprocessors configurable
-   PR \#1504: Bump sqlalchemy from 1.4.23 to ### 1.4.25   PR \#1503: Bump pytest-xdist from 2.2.1 to ### 2.4.0   PR \#1502: Bump alembic from 1.7.1 to ### 1.7.3   PR \#1498: Bump rapidfuzz from 1.5.1 to ### 1.6.2   PR \#1497: Bump notebook from 6.4.3 to ### 6.4.4   PR \#1496: docs/index: Move setup-related topics to configuration
    section
-   PR \#1494: docs: update highlights to introduce the notebook format
-   PR \#1493: docs: revise \"Managing assignment files\" pages
-   PR \#1489: Bump rapidfuzz from 1.4.1 to ### 1.5.1   PR \#1488: Bump traitlets from 5.0.5 to ### 5.1.0   PR \#1487: Bump alembic from 1.6.5 to ### 1.7.1   PR \#1480: Bump sqlalchemy from 1.4.22 to ### 1.4.23   PR \#1478: Bump notebook from 6.4.2 to ### 6.4.3   PR \#1477: Bump notebook from 6.4.1 to ### 6.4.2   PR \#1476: Fix Issue with Courses tab on Multi courses
-   PR \#1475: Bump notebook from 6.4.0 to ### 6.4.1   PR \#1472: Bump sqlalchemy from 1.4.21 to ### 1.4.22   PR \#1470: Update badges in README
-   PR \#1469: Bump python-dateutil from 2.8.1 to ### 2.8.2   PR \#1468: Bump sqlalchemy from 1.4.20 to ### 1.4.21   PR \#1467: Bump sqlalchemy from 1.4.18 to ### 1.4.20   PR \#1466: Bump requests from 2.25.1 to ### 2.26.0   PR \#1458: Lock setup dependencies
-   PR \#1457: Add missing rollbacks to try/except clauses that execute
    db commits
-   PR \#1450: Update autograding\_resources.rst
-   PR \#1444: Remove continuous integration for python 3.6
-   PR \#1442: Bump traitlets from 4.3.3 to ### 5.0.5   PR \#1441: Update pytest requirement from \<6.0.0,\>=4.5 to ### 6.2.4   PR \#1440: Bump pytest-xdist from 1.34.0 to ### 2.2.1   PR \#1438: Validate pre and post convert hooks
-   PR \#1437: Make converter exporter class configurable
-   PR \#1431: Add dependabot configuration
-   PR \#1425: Use NBGRADER\_VALIDATING env var during autograding
-   PR \#1422: Fix docs building
-   PR \#1420: Fix various SQLAlchemy errors and warnings
-   PR \#1419: Update releasing docs and tools
-   PR \#1394: Added CLI for generating solution notebooks
-   PR \#1381: find cell failure when stderr is used
-   PR \#1376: Make preprocessors of generate assignment, autograde and
    generate feedback configurable
-   PR \#1330: Update azure pipelines matrix to add Python 3.8
-   PR \#1329: Update the test matrix on Travis to Python 3.6+
-   PR \#1324: Ensure errors are written to cell outputs to prevent the
    autograder from awarding points for failed tests
-   PR \#1320: Add nbgrader collect \--before-duedate option
-   PR \#1315: ExchangeFetchAssignment deleting the wrong config
-   PR \#1287: Add mypy for type checking
-   PR \#1282: Further type annotations across the codebase
-   PR \#1276: remove db\_assignments db\_students
-   PR \#1274: Further Python 3 type annotations on top-level files
-   PR \#1268: Type annotations for the api
-   PR \#1259: Remove Python 2 compatibility code
-   PR \#1257: Deprecate Python 2 support
-   PR \#1238: Pluggable exchange
-   PR \#1222: CourseDir.format\_path: supports absolute paths in
    nbgrader\_step

Thanks to the following users who submitted PRs or reported issues that
were merged or fixed for the 0.7.0 release:

-   aliniknejad
-   AnotherCodeArtist
-   bbhopesh
-   BertR
-   brichet
-   elesiuta
-   gymreklab
-   HanTeo
-   jgwerner
-   jhamrick
-   jnishii
-   jtpio
-   LaurentHayez
-   liuq
-   lzach
-   nthiery
-   omelnikov
-   QuantumEntangledAndy
-   rkdarst
-   ryanlovett
-   samarthbhargav
-   sigurdurb
-   Tebinski
-   tmetzl
-   Wildcarde
-   willingc
-   ykazakov

## 0.6.x

### 0.6.2

nbgrader version 0.6.2 is a bugfix release. The following PRs were
merged:

-   PR \#1443: Fix broken windows tests
-   PR \#1410: partial credit returns zero when score is zero
-   PR \#1388: Move from travis ci to github actions
-   PR \#1384: Fix migrations.
-   PR \#1369: Pin nbconvert to 5.6.1, traitlets to 4.3.3 and pytest to
    \<### 6.0.0   PR \#1362: Fix migration, grade cells were looking for a
    non-existing column
-   PR \#1356: add SAS codestub and autograde for metakernel based
    non-python kernels
-   PR \#1352: Description of \"what is nbgrader?\"
-   PR \#1343: Update deprecated jquery functions and update jquery
-   PR \#1341: Make format\_path behave the same for absolute paths
-   PR \#1319: use rapidfuzz instead of fuzzywuzzy
-   PR \#1308: docs: Fix formgrader group name in docs
-   PR \#1288: Fixes \#1283: Replace AppVeyor badge with Azure Devops
    badge
-   PR \#1281: Demos using Python3
-   PR \#1249: timestamp\_format raises an exception

Thanks to the following users who submitted PRs or reported issues that
were merged or fixed for the 0.6.1 release:

-   BertR
-   chinery
-   echuber2
-   enisnazif
-   fredcallaway
-   HanTeo
-   jgwerner
-   jhamrick
-   jld23
-   kcranston
-   lzach
-   maxbachmann
-   nklever
-   Patil2099
-   rkdarst
-   tmetzl

### 0.6.1

nbgrader version 0.6.1 is a bugfix release. The following PRs were
merged:

-   PR \#1280: Fix inappropriate use of sum with newer sqlite
-   PR \#1278: Fix course list hanging when exchange has not been
    created
-   PR \#1272: Improve test coverage in auth folder
-   PR \#1270: Add requirements for readthedocs
-   PR \#1267: Improve the error message on the assignments page
-   PR \#1260: Set up CI with Azure Pipelines
-   PR \#1245: Move away from using the internal Traitles API to load
    default configuration.
-   PR \#1243: Fix project name typo
-   PR \#1228: Fix formgrader API
-   PR \#1227: Bump pytest required version to 4.5 for custom marker
    support
-   PR \#1208: Improve coverage of nbgraderformat
-   PR \#1205: Check for newer feedback in nbgrader list
-   PR \#1204: Force generate feedback by default in API
-   PR \#1200: Associate feedback files with unique submission attempts
-   PR \#1197: Do not duplicate assignments when fetching feedback
-   PR \#1196: Fix config warning in ExchangeReleaseAssignment
-   PR \#1194: Update releasing instructions

Thanks to the following users who submitted PRs or reported issues that
were merged or fixed for the 0.6.1 release:

-   BertR
-   enisnazif
-   jhamrick
-   kinow
-   nthiery
-   sir-dio

### 0.6.0

nbgrader version 0.6.0 is a major release, involving over 100 PRs and 60
issues. This includes many bug fixes, small enhancements, and improved
docs. The major new features include:

-   Better support for multiple classes with JupyterHub. In particular,
    a new \"Course List\" extension has been added which provides
    instructors access to separate formgrader instances for all the
    classes they can manage. Additionally, JupyterHub authentication is
    used to control which students have access to which assignments.
-   Better LMS integration (for example, adding a `lms_user_id` column
    in the `Student` table of the database).
-   Better support for feedback. In particular, there is now the ability
    to generate and return feedback to students through nbgrader with
    the `generate_feedback` and `release_feedback` commands, and the
    ability for students to fetch feedback with the `fetch_feedback`
    command. This functionality is also available through the formgrader
    and Assignment List extensions.
-   Instructions for how to do grading inside a Docker container, for
    increased protection against malicious code submitted by students.
-   A new type of nbgrader cell called a \"task\" cell which supports
    more open-ended solutions which may span multiple cells.

**Important**: Users updating from 0.5.x to 0.6.0 should be aware that
they will need to do the following (please make sure to back up your
files before doing so, just in case anything goes wrong!):

-   Update their nbgrader database using `nbgrader db upgrade`.
-   Update the metadata in their assignments using `nbgrader update`.
-   Reinstall the nbgrader extensions (see
    `/user_guide/installation`{.interpreted-text role="doc"}).

Please also note that some of the nbgrader commands have been renamed,
for consistency with the new feedback commands:

-   `nbgrader assign` is now `nbgrader generate_assignment`
-   `nbgrader release` is now `nbgrader release_assignment`
-   `nbgrader fetch` is now `nbgrader fetch_assignment`

The full list of PRs is:

-   PR \#1191: Allow access to formgrader when not using JuptyerHub auth
-   PR \#1190: Add JupyterHub demos
-   PR \#1186: Remove student\_id and change root to cache, permission
    check to only execute
-   PR \#1184: Move the fetch feedback API from formgrader to
    assignment\_list
-   PR \#1183: Feedback: update fetch\_feedback command line help
-   PR \#1180: Fix versions of pytest and nbconvert
-   PR \#1179: Add CourseDir.student\_id\_exclude option to exclude
    students
-   PR \#1169: Fix minor typo in js extension helper text
-   PR \#1164: assignment\_dir: Add into several missing places
-   PR \#1152: Rename \'nbgrader fetch\' to \'nbgrader
    fetch\_assignment\'
-   PR \#1151: Rename \'nbgrader release\' to \'nbgrader
    release\_assignment\'
-   PR \#1147: Add test to ensure that db upgrade succeeds before
    running assign
-   PR \#1145: Rename nbgrader feedback to nbgrader generate\_feedback
-   PR \#1140: A few more updates to the docs for multiple classes
-   PR \#1139: Additional docs sanitization
-   PR \#1138: Ensure that cell type changes result in valid nbgrader
    metadata
-   PR \#1137: Rename \"nbgrader assign\" to \"nbgrader
    generate\_assignment\"
-   PR \#1135: section on grading in docker container
-   PR \#1131: Better support for multiple classes
-   PR \#1127: Better documentation of nbgrader\_config.py
-   PR \#1126: Remove the third party resources page
-   PR \#1125: Check that the course directory is a subdirectory of the
    notebook dir
-   PR \#1124: Only run nbextensions tests on oldest and newest versions
    of python
-   PR \#1123: Ensure course directory root path has no trailing slashes
-   PR \#1122: Fix incorrect usage of Exchange.course\_id
-   PR \#1121: Fix logfile
-   PR \#1120: Integrate feedback distribution within nbgrader
-   PR \#1119: added a sanatizing step to the doc creation.
-   PR \#1118: Integrate course\_id into the api and apps
-   PR \#1116: Autograde & Assign: create missing students/assignments
    by default
-   PR \#1115: Fix typo in tmp filename prefix in conftest.py
-   PR \#1114: Documentation for multiple classes
-   PR \#1113: Add a course list extension that shows all courses an
    instructor can manage
-   PR \#1112: Locate all configurable classes for generate\_config
    subcommand
-   PR \#1111: Optional consistency check between owner and student\_id
    upon collect
-   PR \#1110: Systematic use of utils.get\_username instead of \$USER
-   PR \#1109: naming the temporary directories in tests
-   PR \#1108: Extended support for filtering files copied in the
    exchange
-   PR \#1106: Remove testing of python 3.4
-   PR \#1105: Remove extra keys in nbgrader metadata and better schema
    mismatch errors
-   PR \#1102: Only build docs with one version of python
-   PR \#1101: Add jupyter education book to third party resources
-   PR \#1100: Run test in the [python]{.title-ref} group in parallel
    using pytest-xdist
-   PR \#1099: Add course table, add course\_id column to assignment
-   PR \#1098: Customizable student ID in [nbgrader submit]{.title-ref}
-   PR \#1094: Update license
-   PR \#1093: Add authentication plugin support
-   PR \#1090: partial credit for autograde test cells
-   PR \#1088: Remove version requirement from urllib3
-   PR \#1084: Fix miscellaneous bugs
-   PR \#1080: compatibility with SQLAlchemy 1.3+
-   PR \#1075: Give ExecutePreprocessor the Traitlets config during
    validation
-   PR \#1071: student and assignment selection in exportapp implemented
-   PR \#1064: Validate all cells
-   PR \#1061: Set env var NBGRADER\_VALIDATING when validating
-   PR \#1054: Raise error when executed task fails
-   PR \#1053: Remove changes to sitecustomize.py and dependency on
    invoke
-   PR \#1051: Remove spellcheck and enchant dependency
-   PR \#1040: Restrict access for students to different courses
-   PR \#1036: Add a general lms user id column to the student table
-   PR \#1032: fix: return info of reper function is wrong in api.py
-   PR \#1029: Documentation fix to add info re: timeout errors.
-   PR \#1028: Some improvements to the contributor list script
-   PR \#1026: Mark test\_same\_part\_navigation as flaky
-   PR \#1025: Fixing failing tests, take 2
-   PR \#1024: Fix deprecation warning with timezones
-   PR \#1023: Ensure nbgrader list still works with random strings
-   PR \#1021: Fix tests, all of which are failing :(
-   PR \#1019: Make nbgrader quickstart work with existing directories
-   PR \#1018: Add missing close \> for url to display correctly
-   PR \#1017: Fix all redirection
-   PR \#1014: a mistake in comment
-   PR \#1005: Add random string to submission filenames for better
    hiding
-   PR \#1002: Change to notebook directory when validating (repeat of
    \#880)
-   PR \#1001: Allow setting a different assignment dir for students
    than the root notebook directory
-   PR \#1000: Allow instructors to share files via shared group id
-   PR \#994: Add link to jupyter in education map
-   PR \#991: Fix broken documentation
-   PR \#990: Include section on mocking (autograding resources)
-   PR \#989: Update developer installation instructions
-   PR \#984: Adding global graded tasks
-   PR \#975: Fix the link to the activity magic
-   PR \#972: Use mathjax macro for formgrader
-   PR \#967: Added note in FAQ about changing cell ids
-   PR \#964: Added \"if \_\_name\_\_ == \"\_\_main\_\_\":\"
-   PR \#963: Add third party resources to the documentation
-   PR \#962: Add grant\_extension method to the gradebook
-   PR \#959: Allow apps to use -f and \--force
-   PR \#958: Do some amount of fuzzy problem set name matching
-   PR \#957: Remove underscores from task names
-   PR \#955: Ignore .pytest\_cache in .gitignore
-   PR \#954: Fix bug in find\_all\_files that doesn\'t properly ignore
    directories
-   PR \#953: update log.warn (deprecated) to log.warning
-   PR \#948: Move config file generation to a separate app
-   PR \#947: Exclude certain assignment files from being overwritten
    during autograding
-   PR \#946: Fix failing tests
-   PR \#937: Strip whitespace from assignment, student, and course ids
-   PR \#936: Switch from PhamtomJS to Firefox
-   PR \#934: Skip filtering notebooks when ExchangeSubmit.strict ==
    True
-   PR \#933: Fix failing tests
-   PR \#932: Prevent assignments from being created with invalid names
-   PR \#911: Update installation.rst
-   PR \#909: Friendlier error messages when encountering a schema
    mismatch
-   PR \#908: Better validation errors when cell type changes
-   PR \#906: Resolves issues with UTF-8
-   PR \#905: Update changelog and rebuild docs from ### 0.5.4   PR \#900: Improve issue template to explain logic behind filling it
    out
-   PR \#899: Help for csv import
-   PR \#897: Give more details on how to use formgrader and jupyterhub
-   PR \#892: Format code blocks in installation instructions
-   PR \#886: Add nbval for non-Windows tests/CI
-   PR \#877: Create issue\_template.md
-   PR \#871: Fix NbGraderAPI.timezone handling
-   PR \#870: added java, matlab, and octave codestubs to
    clearsolutions.py
-   PR \#853: Update changelog from 0.5.x releases
-   PR \#838: Fetch multiple assignments in one command

Huge thanks to the following users who submitted PRs or reported issues
that were merged or fixed for the 0.6.0 release:

-   00Kai0
-   Alexanderallenbrown
-   aliandra
-   amellinger
-   BertR
-   Carreau
-   cdvv7788
-   Ciemaar
-   consideRatio
-   damianavila
-   danielmaitre
-   DavidNemeskey
-   davidpwilliamson
-   davis68
-   ddbourgin
-   ddland
-   dechristo
-   destitutus
-   dsblank
-   edouardtheron
-   fenwickipedia
-   fm75
-   FranLucchini
-   gertingold
-   hcastilho
-   JanBobolz
-   jedbrown
-   jhamrick
-   jnak12
-   kcranston
-   kthyng
-   lgpage
-   liffiton
-   mikezawitkowski
-   mozebdi
-   mpacer
-   nabriis
-   nthiery
-   perllaghu
-   QuantumEntangledAndy
-   rgerkin
-   rkdarst
-   Ruin0x11
-   rwest
-   ryanlovett
-   samhinshaw
-   Sefriol
-   sigurdurb
-   slel
-   soldis
-   swarnava
-   takluyver
-   thotypous
-   vahtras
-   VETURISRIRAM
-   vidartf
-   willingc
-   yangkky
-   zonca

## 0.5.x

### 0.5.6

nbgrader version 0.5.6 is a small release that only unpins the version
of IPython and Jupyter console.

### 0.5.5

nbgrader version 0.5.5 is a release for the Journal of Open Source
education, with the following PRs merged:

-   PR \#1057: Ensure consistency in capitalizing Jupyter Notebook
-   PR \#1049: Update test builds on Travis
-   PR \#1047: JOSE paper bib updates
-   PR \#1045: Dev requirements and spelling tests
-   PR \#1016: Fix anaconda link
-   PR \#973: Create a paper on nbgrader

Thanks to the following users who submitted PRs or reported issues that
were fixed for the 0.5.5 release:

-   jedbrown
-   jhamrick
-   swarnava
-   willingc

### 0.5.4

nbgrader version 0.5.4 is a bugfix release, with the following PRs
merged:

-   PR \#898: Make sure validation is run in the correct directory
-   PR \#895: Add test and fix for parsing csv key names with spaces
-   PR \#888: Fix overwritekernelspec preprocessor and update tests
-   PR \#880: change directory when validating notebooks
-   PR \#873: Fix issue with student dictionaries when assignments have
    zero points

Thanks to the following users who submitted PRs or reported issues that
were fixed for the 0.5.4 release:

-   jcsutherland
-   jhamrick
-   lgpage
-   misolietavec
-   mpacer
-   ncclementi
-   randy3k

### 0.5.3

nbgrader version 0.5.3 is a bugfix release, with the following PRs
merged:

-   PR \#868: Fix travis to work with trusty
-   PR \#867: Change to the root of the course directory before running
    nbgrader converters
-   PR \#866: Set nbgrader url prefix to be relative to notebook\_dir
-   PR \#865: Produce warnings if the exchange isn\'t set up correctly
-   PR \#864: Fix link to jupyterhub docs
-   PR \#861: fix the html to ipynb in docs

Thanks to the following users who submitted PRs or reported issues that
were fixed for the 0.5.3 release:

-   jhamrick
-   misolietavec
-   mpacer
-   rdpratti

### 0.5.2

nbgrader version 0.5.2 is a bugfix release, with most of the bugs being
discovered and subsequently fixed by the sprinters at SciPy 2017! The
following PRs were merged:

-   PR \#852: Fix spelling wordlist, again
-   PR \#850: Include extension with feedback template filename
-   PR \#848: Add links to the scipy talk
-   PR \#847: Fix html export config options to avoid warnings
-   PR \#846: Disallow negative point values
-   PR \#845: Don\'t install assignment list on windows
-   PR \#844: Reveal ids if names aren\'t set
-   PR \#843: Update spelling wordlist
-   PR \#840: Avoid extension errors when exchange is missing
-   PR \#839: Always raise on convert failure
-   PR \#837: Report mismatch extension versions
-   PR \#836: Add documentation for course\_id and release
-   PR \#835: DOC: correct Cell Toolbar location
-   PR \#833: Include quickstart .ipynb header
-   PR \#831: Fix typo on Managing assignment docs
-   PR \#830: Print out app subcommands by default
-   PR \#825: Add directory structure example
-   PR \#824: Add FAQ sections
-   PR \#823: Typo fix.
-   PR \#819: Update install instructions
-   PR \#816: Add jupyter logo
-   PR \#802: Fix bug with autograding when there is no timestamp

Thanks to the following users who submitted PRs or reported issues that
were fixed for the 0.5.2 release:

-   arcticbarra
-   BjornFJohansson
-   hetland
-   ixjlyons
-   jhamrick
-   katyhuff
-   ksunden
-   lgpage
-   ncclementi
-   Ruin0x11

### 0.5.1

nbgrader version 0.5.1 is a bugfix release mainly fixing an issue with
the formgrader. The following PRs were merged:

-   PR \#792: Make sure relative paths to source and release dirs are
    correct
-   PR \#791: Use the correct version number in the docs

### 0.5.0

nbgrader version 0.5.0 is another very large release with some very
exciting new features! The highlights include:

-   The formgrader is now an extension to the notebook, rather than a
    standalone service.
-   The formgrader also includes functionality for running
    `nbgrader assign`, `nbgrader release`, `nbgrader collect`, and
    `nbgrader autograde` directly from the browser.
-   A new command `nbgrader zip_collect`, which helps with collecting
    assignment files downloaded from a LMS.
-   Hidden test cases are now supported.
-   A lot of functionality has moved into standalone objects that can be
    called directly from Python, as well as a high-level Python API in
    `nbgrader.apps.NbGraderAPI` (see
    `/api/high_level_api`{.interpreted-text role="doc"}).
-   A new **Validate** notebook extension, which allows students to
    validate an assignment notebook from the notebook itself (this is
    equivalent functionality to the \"Validate\" button in the
    Assignment List extension, but without requiring students to be
    using the Assignment List).
-   A new command `nbgrader db upgrade`, which allows you to migrate
    your nbgrader database to the latest version without having to
    manually execute SQL commands.
-   New cells when using the Create Assignment extension will
    automatically given randomly generated ids, so you don\'t have to
    set them yourself.
-   You can assign extra credit when using the formgrader.

**Important**: Users updating from 0.4.x to 0.5.0 should be aware that
they will need to update their nbgrader database using
`nbgrader db upgrade` and will need to reinstall the nbgrader extensions
(see `/user_guide/installation`{.interpreted-text role="doc"}).
Additionally, the configuration necessary to use the formgrader with
JupyterHub has changed, though it is now much more straightforward (see
`/configuration/jupyterhub_config`{.interpreted-text role="doc"}).

The full list of merged PRs includes:

-   PR \#789: Fix more inaccurate nbextension test failures after reruns
-   PR \#788: Fix inaccurate nbextension test failures after reruns
-   PR \#787: Fix slow API calls
-   PR \#786: Update documentation for nbgrader as a webapp
-   PR \#784: Fix race condition in validate extension tests
-   PR \#782: Implement nbgrader as a webapp
-   PR \#781: Assign missing notebooks a score of zero and mark as not
    needing grading
-   PR \#780: Create a new high-level python API for nbgrader
-   PR \#779: Update the year!
-   PR \#778: Create and set permissions for exchange directory when
    using `nbgrader release`
-   PR \#774: Add missing config options
-   PR \#772: Standalone versions of nbgrader assign, autograde, and
    feedback
-   PR \#771: Fix mathjax rendering
-   PR \#770: Better cleanup when nbconvert-based apps crash
-   PR \#769: Fix nbgrader validate globbing for real this time
-   PR \#768: Extra credit
-   PR \#766: Make sure validation works with notebook globs
-   PR \#764: Migrate database with alembic
-   PR \#762: More robust saving of the notebook in create assignment
    tests
-   PR \#761: Validate assignment extension
-   PR \#759: Fix nbextension tests
-   PR \#758: Set random cell ids
-   PR \#756: Fix deprecations and small bugs
-   PR \#755: Fast validate
-   PR \#754: Set correct permissions when submitting assignments
-   PR \#752: Add some more informative error messages in zip collect
-   PR \#751: Don\'t create the gradebook database until formgrader is
    accessed
-   PR \#750: Add documentation for how to pass numeric ids
-   PR \#747: Skip over students with empty submissions
-   PR \#746: Fix bug with \--to in custom exporters
-   PR \#738: Refactor the filtering of existing submission notebooks
    for formgrader
-   PR \#735: Add DataTables functionality to existing formgrade tables
-   PR \#732: Fix the collecting of submission files for multiple
    attempts of multiple notebook assignments
-   PR \#731: Reset late submission penalty before checking if
    submission is late or not
-   PR \#717: Update docs regarding solution delimeters
-   PR \#714: Preserve kernelspec when autograding
-   PR \#713: Use new exchange functionality in assignment list app
-   PR \#712: Move exchange functionality into non-application classes
-   PR \#711: Move some config options into a CourseDirectory object.
-   PR \#709: Fix formgrader tests link for 0.4.x branch (docs)
-   PR \#707: Force rerun nbgrader commands
-   PR \#704: Fix nbextension tests
-   PR \#701: Set proxy-type=none in phantomjs
-   PR \#700: use check\_call for extension installation in tests
-   PR \#698: Force phantomjs service to terminate in Linux
-   PR \#696: Turn the gradebook into a context manager
-   PR \#695: Use sys.executable when executing nbgrader
-   PR \#693: Update changelog from ### 0.4.0   PR \#681: Hide tests in \"Autograder tests\" cells
-   PR \#622: Integrate the formgrader into the notebook
-   PR \#526: Processing of LMS downloaded submission files

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.5.0 release:

-   AnotherCodeArtist
-   dementrock
-   dsblank
-   ellisonbg
-   embanner
-   huwf
-   jhamrick
-   jilljenn
-   lgpage
-   minrk
-   suchow
-   Szepi
-   whitead
-   ZelphirKaltstahl
-   zpincus

## 0.4.x

### 0.4.0

nbgrader version 0.4.0 is a substantial release with lots of changes and
several new features. The highlights include:

-   Addition of a command to modify students and assignments in the
    database (`nbgrader db`)
-   Validation of nbgrader metadata, and a command to automatically
    upgrade said metadata from the previous version (`nbgrader update`)
-   Support for native Jupyter nbextension and serverextension
    installation, and deprecation of the `nbgrader nbextension` command
-   Buttons to reveal students\' names in the formgrader
-   Better reporting of errors and invalid submissions in the
    \"Assignment List\" extension
-   Addition of a menu to change between different courses in the
    \"Assignment List\" extension
-   Support to run the formgrader as an official JupyterHub service
-   More flexible code and text stubs when creating assignments
-   More thorough documentations

**Important**: Users updating from 0.3.x to 0.4.0 should be aware that
they will need to update the metadata in their assignments using
`nbgrader update` and will need to reinstall the nbgrader extensions
(see `/user_guide/installation`{.interpreted-text role="doc"}).
Additionally, the configuration necessary to use the formgrader with
JupyterHub has changed, though it is now much less brittle (see
`/configuration/jupyterhub_config`{.interpreted-text role="doc"}).

The full list of merged PRs includes:

-   PR \#689: Add cwd to path for all nbgrader apps
-   PR \#688: Make sure the correct permissions are set on released
    assignments
-   PR \#687: Add display\_data\_priority option to GetGrades
    preprocessor
-   PR \#679: Get Travis-CI to build
-   PR \#678: JUPYTERHUB\_SERVICE\_PREFIX is already the full URL prefix
-   PR \#672: Undeprecate \--create in assign and autograde
-   PR \#670: Fix deprecation warnings for config options
-   PR \#665: Preventing URI Encoding of the base-url in the
    assignment\_list extension
-   PR \#656: Update developer installation docs
-   PR \#655: Fix saving notebook in create assignment tests
-   PR \#652: Make 0.4.0 release
-   PR \#651: Update changelog with changes from 0.3.3 release
-   PR \#650: Print warning when no config file is found
-   PR \#649: Bump the number of test reruns even higher
-   PR \#646: Fix link to marr paper
-   PR \#645: Fix coverage integration by adding codecov.yml
-   PR \#644: Add AppVeyor CI files
-   PR \#643: Add command to update metadata
-   PR \#642: Handle case where points is an empty string
-   PR \#639: Add and use a Gradebook contextmanager for DbApp and DbApp
    tests
-   PR \#637: Update conda channel to conda-forge
-   PR \#635: Remove conda recipe and document nbgrader-feedstock
-   PR \#633: Remove extra level of depth in schema per \@ellisonbg
-   PR \#630: Don\'t fail `test_check_version` test on
    `'import sitecustomize' failed error`
-   PR \#629: Update changelog for 0.3.1 and ### 0.3.2   PR \#628: Make sure to include schema files
-   PR \#625: Add \"nbgrader db\" app for modifying the database
-   PR \#623: Move server extensions into their own directory
-   PR \#621: Replace tabs with spaces in installation docs
-   PR \#620: Document when needs manual grade is set
-   PR \#619: Add CI tests for python 3.6
-   PR \#618: Implement formgrader as a jupyterhub service
-   PR \#617: Add ability to show student names in formgrader
-   PR \#616: Rebuild docs
-   PR \#615: Display assignment list errors
-   PR \#614: Don\'t be as strict about solution delimeters
-   PR \#613: Update FAQ with platform information
-   PR \#612: Update to new traitlets syntax
-   PR \#611: Add metadata schema and documentation
-   PR \#610: Clarify formgrader port and suppress notebook output
-   PR \#607: Set instance variables in base auth class before running
    super init
-   PR \#598: Conda recipe - nbextension link / unlink scripts
-   PR \#597: Re-submitting nbextension work from previous PR
-   PR \#594: Revert \"Use jupyter nbextension/serverextension for
    installation/activation\"
-   PR \#591: Test empty and invalid timestamp strings
-   PR \#590: Processing of invalid `notebook_id`
-   PR \#585: Add catches for empty timestamp files and invalid
    timestamp strings
-   PR \#581: Update docs with invoke test group commands
-   PR \#571: Convert readthedocs links for their .org -\> .io migration
    for hosted projects
-   PR \#567: Handle autograding failures better
-   PR \#566: Add support for true read-only cells
-   PR \#565: Add option to nbgrader fetch for replacing missing files
-   PR \#564: Update documentation pertaining to the assignment list
    extension
-   PR \#563: Add ability to switch between courses in assignment list
    extension
-   PR \#562: Add better support to transfer apps for multiple courses
-   PR \#550: Add documentation regarding how validation works
-   PR \#545: Document how to customize the student version of an
    assignment
-   PR \#538: Use official HubAuth from JupyterHub
-   PR \#536: Create a \"nbgrader export\" command
-   PR \#523: Allow code stubs to be language specific

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.4.0 release:

-   adamchainz
-   AstroMike
-   ddbourgin
-   dlsun
-   dsblank
-   ellisonbg
-   huwf
-   jhamrick
-   lgpage
-   minrk
-   olgabot
-   randy3k
-   whitead
-   whositwhatnow
-   willingc

## 0.3.x

### 0.3.3

Version 0.3.3 of nbgrader is a minor bugfix release that fixes an issue
with running `nbgrader fetch` on JupyterHub. The following PR was merged
for the 0.3.3 milestone:

-   PR \#600: missing sys.executable, \"-m\", on fetch\_assignment

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.3.3 release:

-   alikasamanli
-   hetland

### 0.3.2

Version 0.3.2 of nbgrader includes a few bugfixes pertaining to building
nbgrader on conda-forge.

-   PR \#608: Fix Windows tests
-   PR \#601: Add shell config for invoke on windows
-   PR \#593: Send xsrf token in the X-XSRF-Token header for ajax
-   PR \#588: `basename` to wordslist
-   PR \#584: Changes for Notebook v4.3 tests

Thanks to lgpage, who made all the changes necessary for the 0.3.2
release!

### 0.3.1

Version 0.3.1 of nbgrader includes a few bugfixes pertaining to
PostgreSQL and updates to the documentation. The full list of merged PRs
is:

-   PR \#561: Close db engine
-   PR \#548: Document how to install the assignment list extension for
    all users
-   PR \#546: Make it clearer how to set due dates
-   PR \#535: Document using JupyterHub with SSL
-   PR \#534: Add advanced topics section in the docs
-   PR \#533: Update docs on installing extensions

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.3.1 release:

-   ddbourgin
-   jhamrick
-   whositwhatnow

### 0.3.0

Version 0.3.0 of nbgrader introduces several significant changes. Most
notably, this includes:

-   Windows support
-   Support for Python 3.5
-   Support for Jupyter Notebook 4.2
-   Allow assignments and students to be specified in
    `nbgrader_config.py`
-   Addition of the \"nbgrader quickstart\" command
-   Addition of the \"nbgrader extension uninstall\" command
-   Create a nbgrader conda recipe
-   Add an entrypoint for late penalty plugins

The full list of merged PRs is:

-   PR \#521: Update to most recent version of invoke
-   PR \#512: Late penalty plugin
-   PR \#510: Fix failing windows tests
-   PR \#508: Run notebook/formgrader/jupyterhub on random ports during
    tests
-   PR \#507: Add a FAQ
-   PR \#506: Produce a warning if no coverage files are produced
-   PR \#505: Use .utcnow() rather than .now()
-   PR \#498: Add a section on autograding wisdom
-   PR \#495: Raise an error on iopub timeout
-   PR \#494: Write documentation on creating releases
-   PR \#493: Update nbgrader to be compatible with notebook version 4.2
-   PR \#492: Remove generate\_hubapi\_token from docs
-   PR \#490: Temporarily pin to notebook 4.1
-   PR \#489: Make sure next/prev buttons use correct base\_url
-   PR \#486: Add new words to wordlist
-   PR \#485: Update README gif links after docs move into nbgrader
-   PR \#477: Create a conda recipe
-   PR \#473: More helpful default comment box message
-   PR \#470: Fix broken links
-   PR \#467: unpin jupyter-client
-   PR \#466: Create nbgrader quickstart command
-   PR \#465: Confirm no SSL when running jupyterhub
-   PR \#464: Speed up tests
-   PR \#461: Add more prominent links to demo
-   PR \#460: Test that other kernels work with nbgrader
-   PR \#458: Add summary and links to resources in docs
-   PR \#457: Update formgrader options to not conflict with the
    notebook
-   PR \#455: More docs
-   PR \#454: Simplify directory and notebook names
-   PR \#453: Merge user guide into a few files
-   PR \#452: Improve docs reliability
-   PR \#451: Execute documentation notebooks manually
-   PR \#449: Allow \--assignment flag to be used with transfer apps
-   PR \#448: Add \--no-execute flag to autogradeapp.py
-   PR \#447: Remove option to generate the hubapi token
-   PR \#446: Make sure perms are set correctly by nbgrader submit
-   PR \#445: Skip failures and log to file
-   PR \#444: Fix setup.py
-   PR \#443: Specify assignments and students in the config file
-   PR \#442: Fix build errors
-   PR \#430: Reintroduce flit-less setup.py
-   PR \#425: Enable 3.5 on travis.
-   PR \#421: Fix Contributor Guide link
-   PR \#414: Restructure user guide TOC and doc flow to support new
    users
-   PR \#413: Windows support
-   PR \#411: Add tests for https
-   PR \#409: Make a friendlier development install
-   PR \#408: Fix formgrader to use course directory
-   PR \#407: Add \--no-metadata option to nbgrader assign
-   PR \#405: nbgrader release typo
-   PR \#402: Create a Contributor Guide in docs
-   PR \#397: Port formgrader to tornado
-   PR \#395: Specify root course directory
-   PR \#387: Use sys.executable to run suprocesses
-   PR \#386: Use relative imports
-   PR \#384: Rename the html directory to formgrader
-   PR \#381: Access notebook server of formgrader user

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.3.0 release:

-   alchemyst
-   Carreau
-   ellisonbg
-   ischurov
-   jdfreder
-   jhamrick
-   jklymak
-   joschu
-   lgpage
-   mandli
-   mikebolt
-   minrk
-   olgabot
-   sansary
-   svurens
-   vinaykola
-   willingc

## 0.2.x

### 0.2.2

Adds some improvements to the documentation and fixes a few small bugs:

-   Add requests as a dependency
-   Fix a bug where the \"Create Assignment\" extension was not
    rendering correctly in Safari
-   Fix a bug in the \"Assignment List\" extension when assignment names
    had periods in them
-   Fix integration with JupyterHub when SSL is enabled
-   Fix a bug with computing checksums of cells that contain UTF-8
    characters under Python 2

### 0.2.1

Fixes a few small bugs in v0.2.0:

-   Make sure checksums can be computed from cells containing unicode
    characters
-   Fixes a bug where nbgrader autograde would crash if there were any
    cells with blank grade ids that weren\'t actually marked as nbgrader
    cells (e.g. weren\'t tests or read-only or answers)
-   Fix a few bugs that prevented postgres from being used as the
    database for nbgrader

### 0.2.0

Version 0.2.0 of nbgrader primarily adds support for version 4.0 of the
Jupyter notebook and associated project after The Big Split. The full
list of major changes are:

-   Jupyter notebook 4.0 support
-   Make it possible to run the formgrader inside a Docker container
-   Make course\_id a requirement in the transfer apps (list, release,
    fetch, submit, collect)
-   Add a new assignment list extension which allows students to list,
    fetch, validate, and submit assignments from the notebook dashboard
    interface
-   Auto-resize text boxes when giving feedback in the formgrader
-   Deprecate the BasicConfig and NbGraderConfig classes in favor of a
    NbGrader class

Thanks to the following contributors who submitted PRs or reported
issues that were merged/closed for the 0.2.0 release:

-   alope107
-   Carreau
-   ellisonbg
-   jhamrick
-   svurens

## 0.1.0

I\'m happy to announce that the first version of nbgrader has (finally)
been released! nbgrader is a tool that I\'ve been working on for a
little over a year now which provides a suite of tools for creating,
releasing, and grading assignments in the Jupyter notebook. So far,
nbgrader has been used to grade assignments for the class I ran in the
spring, as well as two classes that Brian Granger has taught.

If you have any questions, comments, suggestions, etc., please do open
an issue on the bugtracker. This is still a very new tool, so I am sure
there is a lot that can be improved upon!

Thanks so much to all of the people who have contributed to this release
by reporting issues and/or submitting PRs:

-   alope107
-   Carreau
-   ellachao
-   ellisonbg
-   ivanslapnicar
-   jdfreder
-   jhamrick
-   jonathanmorgan
-   lphk92
-   redSlug
-   smeylan
-   suchow
-   svurens
-   tasilb
-   willingc
