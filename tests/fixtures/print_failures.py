"""Print JUnit failures ascii-safe."""
import glob
import xml.etree.ElementTree as ET

for fp in glob.glob(
    "android/app/build/test-results/testDebugUnitTest/"
    "TEST-com.trueway.app.data.SqlitePackSourceTest.xml"
):
    r = ET.parse(fp).getroot()
    for tc in r.iter("testcase"):
        for f in list(tc):
            print("TEST:", tc.get("name"))
            print("MSG:", ascii(f.get("message") or "")[:400])
