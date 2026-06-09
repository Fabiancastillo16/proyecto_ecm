import requests
import pandas as pd

url = "https://sis2.cat.com/api/ws-all/ServiceSoftwareFilesRemoteServices/serialNumber/SKH00662?profileId=2"

token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjREWFlYTk9BbThmeC0zU2w2UUxEbTlFbGZ2R0c3amd3U0ZheDdyOWVLY2siLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI3YzdjNDUzMy0wOTkzLTRjODUtYjM2OC0zOTlkMTU1NDc2Y2QiLCJpc3MiOiJodHRwczovL3NpZ25pbi5jYXQuY29tL3RmcC80ZjBmMTlkMC1mNDRjLTRhMDMtYjhjYi1hYjMyN2JkMmIxMmIvYjJjXzFhX3AyX3YxX3NpZ25pbl9wcm9kL3YyLjAvIiwiZXhwIjoxNzc4NjIyMjQ0LCJuYmYiOjE3Nzg2MTg2NDQsImNsaWVudF9pZCI6IjdjN2M0NTMzLTA5OTMtNGM4NS1iMzY4LTM5OWQxNTU0NzZjZCIsImNhdGFmbHRuY2xhc3MiOiJETFIiLCJjYXRsb2dpbmlkIjoicjEyMGZjNDIiLCJjYXRyZWNpZCI6IlBTUC0wMDBCRUU3OSIsImNhdGFmbHRuY29kZSI6IjAwNSIsImNvdW50cnkiOiJDTCIsImVtYWlsX2FkZHJlc3MiOiJGYWJpYW4uQ2FzdGlsbG9AZmlubmluZy5jb20iLCJzdWIiOiIwNmQ2ZDFmYy03NjExLTQ0ZDYtYjVmZS0wYTMzNzQ0NmFmYTMiLCJuYW1lIjoiRmFiaWFuIENhc3RpbGxvIiwiZ2l2ZW5fbmFtZSI6IkZhYmlhbiIsImZhbWlseV9uYW1lIjoiQ2FzdGlsbG8iLCJjb21wYW55IjoiRklOTklORyBDSElMRSIsImNhdGN1cGlkIjoiOTk4OTc0NjEyMCIsInByZWZlcnJlZExhbmd1YWdlIjoiZXMiLCJjYXRhZmx0bm9yZ2NvZGUiOiJSMTIwIiwiY2F0dG9wbGV2ZWxvcmdjb2RlIjoiUjEyMCIsInRpZCI6IjRmMGYxOWQwLWY0NGMtNGEwMy1iOGNiLWFiMzI3YmQyYjEyYiIsInRmcCI6IkIyQ18xQV9QMl9WMV9TaWduSW5fUHJvZCIsImxhbmd1YWdlIjoiZXMtVVMiLCJhenAiOiI3YzdjNDUzMy0wOTkzLTRjODUtYjM2OC0zOTlkMTU1NDc2Y2QiLCJ2ZXIiOiIxLjAiLCJpYXQiOjE3Nzg2MTg2NDR9.Fpgu38D5IuECEqYqiq8kT6DKB-GVc1m2BDuMfqp7PkTBetNEDOAOpULPTN7ZKQdB0DhkHIeLElFPudKUoVHTJE_BmX80mWBzmefkCoPDESHGU3M1AfqPZRZl0vVtHPENcPYWP0-c6ZmK38F7Q2H-kMbU8XLcX4Fh593SeoifJKiEpgQMb0X8ZOsLVWbrD1Hn68IBzWKdeldovef4LbC9KNtvtyV7I_4z8gxYo92GUXCf5Ht5VDcQ-5YU-64gDxoPiY_KSkzgC3tu_AHv4-OZX0ycCY8rReSVvTUrPJ5Gb09iaK20VJjUolyoPSRvkFMjUYjdpjYmecrIKUyBUmBm7A"
session = requests.Session()

session.headers.update({
    "Authorization": f"Bearer {token}",
    "Accept": "application/servicesoftwarefileservice-v3+json",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://sis2.cat.com/",
    "Origin": "https://sis2.cat.com"
})

session.cookies.update({
    "JSESSIONID": "6FD6D31B219B4E34D4F6CE0CE86B581E",
    "Sis2_Login": "version=2&data=2iFeHUJsivRY9Lu52Ey8HwB+JwyPw2BWli2Ovu9gKj8H5Pk3BhJfvdqptgM+1wp9bRA6DxSHLBhdhlOX1Fk077bJQspnvl7HbNqJXsLTqAVPnipLeRz7aY9M9h3pxkdaHfHgXXc35SK38HqzWM3vzV0c/J3QPy/ubnE3LVnC+KV0u3MyFnXEk2XR33zpzCnpMOa3OVGt2ojVM7mJK1EjMQ4CILvgKxhj4ZbpAzg1mB849TDes6KXwRVijbVzstIY6MUO4ZsDsRNGJE5YUyhl5eg5kmKTa7KZ0rX6U6OwvEvko7UCpCAFLFXB/F8Lnd3A9aoJMIZ7noWK6QkYLz79qTqAU8gKulSXJVFTaX1TgiLilCtsDKy7j98osM5gPTm2eESeFdHJrVxQ6gaoy55H13vgBEzjCj7bXscldRqQmgMP7LGSZm88AoMJ7dtqvtAvTZiIYqUCz3VZ67ULYPairMLdb5M5XZJ3XZpiK97xx8BJsYONY2oqwvZN4LUR8W48iqfR48gLoQDrhwgVi1d5vScMeB2P/FMlaGEnlyuzAzsg9rYWwJlfXwrm5MQyJFUiEhjdjbgjlREWbmEIO/gNVIgzQOM7zAPmY6/Wu9/d67NzYBjuJoJ9IomIYGylf6Nu9REeaTOJVJ3lwOiBQAnGgv3rigggnVfMwb1zJltqbX8+ojLB4Eiac48bh164fXq16yD7vb/q3b3eYPfhsAPtCrKnJ08xqs0CgSPXvWt9xRDHlR7zTb1nhHK6YnnXSW1kB5tQyHpTNJJokE48mG55idku/3z4dUmiHFooyXGYVORgcHx5Wj+ht8kObN7CeMIf7vBLpnQwhjW6ain/rsyLTtRpsSPzREqA9DmLGTrWQ+OjKNGNuM35MNQUfqjKLTymdOQh5M6PTTEcP4cWvo5ieMRz5kcR/KcGYlwWEENcLE84D7xycqGioVv7tmhL+8O9e96H28TMdLUyLPz6WZe/Oh5/k7iubr22V6q/PXywWCapikT+mwplGlSkAR+b9duYF/TGIRzG9CtGIKXBUBPvobpgjJoaaypC+fJJ8GsCTYV3zuzCF8wVaGLMCsQMBywf3L4RKrDeQmdScnDemoxfjtKmX5vDMFUT/Dfq9VNE4y5ydmGygr0O05h/meGjgMR5G8Rx3JFqJw5J4lFxvuTcIpf5LwpVil2CeYZ80uRjsFCmL0k3mS+71roI7F5XKMHJkprhJcR7NMAG+GicAqDNlZLQCi6Qpk5MjjgNdgF9fciIPJbqaK2vbox14LHtUgJ8JAI/ghf0nBmHg/WEAWjttnh11RZ7g2ueCqtDakVJulO70KoUAgAsdYub3HDN8txFV0qH0AfHnosZgtodNjVLoRrGhLuQpC/lpNnaO9bkJFDtY+8PASasrbm4TYW30YvnuG4SprSBHve/GKpbU3j/oVn9oD0q9obP5yB2RpcnUxKeLgtk7eEWAjPnq3JYsDrPwDWruKvYDfkOrGM/hS7TJV90n2Y+4ouG9UVdGLp7yrFQitGqeGu0oH8ZfalDLwVf5AhP3KUALeJR/e511tB1dsNRlMOQAGtIUsMdV7s/iZIBg7IT24ezFBj6f1BjPIv9AY6t8vEDMbPLUDL7rUdVn17vPhKUKbCCbUpoN4rllD7ss2hAQ5+2RhPOEqKZUaagxQYZazbI6DfLCr2F1zFrNC+cp/I8cqVefT812WVWt0o/gOttsXD8HbuVrvWNDIjst0Fi23li1RJagWegv/7AWLTf+S3/baIwYeem/ElVC6XJw/Y7ADMVKHh2UUVwYDd937lj1HITpx5t5spH5UQSB5ziw/Oeq6/UblBnkZ7Cay/N189aXyEWBd5rs5vNCUmsC+fsZF0IznWiLI7N1IHnJ5pbk0zc89HXGz6Bxm1BJltsPO6OnwMtks3aGUGJgpMbtSFm3bLVCwRPnfL+TvhIJS6BgHqpHPCWpUhXe1+rhl8BTqiaTT7QHJFYrJD78MDXaJbz5Nom1C6JBZ1iHS/IPn8c0OdHAPpLmSp+D325rweapIL3BzonWnWfGVmYhavA",
    "Sis2_Refresh": "version=2&data=DygtSL0IsbJZ/1T60/soJGZOZY5Ht9k3xSwdtjGpkDUpSC96l9FfxusrSfVVBJaiKOUbsqb1HHZVRKqT6GfpGTcjW7z5ypjlWTOZ6fE0UsIoosfMN30nfJ98pcawgr8tzFy99qLfRNak+6de7YGbhe5kqTfcuLxp/uZGLcp6tRwHjFCmgwa3S4uL/9Cxm3YMQefLy2BFkLa2Q60DkDwx/un11dreE8TggUzGwnhMP8NTFirrQ6TOYQbbGq4N1LiDMQYidd9OlW0m5MDdX9Z1v7DyRHO+RpC5KLELyVzgLBkulo+VXbjTlOWmh4leuRZS3gky7q3yqqTE+5Kk6JhfvgCs09FaZ+y5MCWh7P4eRUQJzaaoXoGDsJY4fhu+O3aylSvoqNE/7ga7VxpXlC3xhrHsQwI8nBmmE/5goBn00Irc6oECzD2zrOil93yIxA+EI55YzJ42YBDolf4pEpBjBcHCBfhJKE1FE1Mm95jGS+cmcYmDu1DyJuoV+nW+M9P0Na06soEyF0A2aVNVrJBASEha58YR3czEzakaq757ulQy4+s8AvCdlAMhUvsMfJVzLqWgUXDdvr5Oy8EcpXb7lcM98I0wrH9mnGO06Xq39df6x8s3x9w9eMVwHVfw0BJdHhXCn1S7H3PMZ3lEQ610R8AP2hnFPRYQIuKGDimW1G1ZTW15a4v6xOQGfNEPsrjsZ2CN0gs/eGYGSxlXb2NsDkz6yRiUQGTidMGuoLGLSTe0yYSiS7O5ygmY03NFZTlddLDmr0JCWGzaVcAj9k1FMtuyYuaCerDqK5qLA1/nopYQfmo1lSYmnp4ygZ/bGvs6cw/UesK810hl7H0v+4wxSq1G+Xe56/2mWIaAzDWyP3RX+ydmYf0m9EcbRCtAaav64yc9N9ycvpzubH3kjZJndIWb9+IXxkE1SgIbbtNrfn3FtiNyoQgFSNiJnFOPG3IjSsD0xNnAfI2OftugL41cz7wLmoZxWWXlKlXeiuST/npVnccbvP0L6voLPg8CyYcoykFdeLOs4uL3LNeGXScNkkt2Rp6wQDRNGJXktIa7m5lp304WsTXmuK03d53k60r+gH+jEm7sxXyQEcyyY/KkdVttIJ4S4DuygISKel6TaKfIWRR812Be2Qo5puuy5RwgMTJP+bWlULsbpT99ufGQ5nVLI6h5TefahrIlM/kPeBXBfCzZnfLVeBzDmdgZK76LWwgHhRVbBjEzmeswh7EZpSWVyEfUqikP03XisL9UvRkJxjAChKxKG+0hcci1E/czj1U/zQQUbDJJVq1tucRwd6rPUZfVhx3uGljtUTVHT2yOOF9E9Ez3K3wePxbJ02wwP9CxZdWTeW+RGlss9cKVe97Zz9Q0eBhoVuNbNwiUB5GbbJCg0RHdJd/ovD+q/q61lcCgUPk/ol0STelGZe6bieYjZ8QlfJJv0C0rUCpU8iCO6AhYrDIOghCN5kacgya5J/BskKlwKhbfot9V4Q7PMsnJcNpLnixsE5kVTBWevB3ok18cFoXRZSLHdV+kM0HHG5RitFwYOw0SOiKrdS4DegyljBskBS15qRIYvnQHZVPRZPLMzIhIu//yZ5VL9Dx2Hpr0z0KAHplRs66YW1cmqeweBqNovEmxurTP99poOyAYN4dw2h5LeD6BmOok0FzrBxxmWuzYizJpPTJQBqzPTKsEk6OyMa21cdjir5I85Q9zkm3B9hWkDqO7iocVyY6u3bhRYW9nja3JdgUkfRiC1hgZeodooKeotM5+fsfwikhtHY22/5jUrptcR+wFGpLwNbOkZqVB6jxcWiGu3trIP+4f4DSUqz5DqX8t4nBQw3YvHaJYBcHNmd/4orN/9iRHpfgP3Tp41dweNsg6mOnhSsZzLZIi52A1+FPKq2yG+2i3JpX30Bvt7Zr0P/tMIzcJlXbF1YCIFxFnbBPFRWz9PDnXwM0Csrf0aPnie+XPPtM="
})

response = session.get(url)

print("STATUS:", response.status_code)
print("STATUS:", response.status_code)

data = response.json()

# -----------------------------------
# DATOS GENERALES
# -----------------------------------

machine = data.get("machine", {})

machine_info = {
    "serial": machine.get("machineSerialNumber"),
    "make": machine.get("make"),
    "dealer": machine.get("dealer", {}).get("name", {}).get("name")
}

print("\nMACHINE INFO")
print(machine_info)

# -----------------------------------
# ECMs
# -----------------------------------

rows = []

for ecm in data.get("ecms", []):

    installed = ecm.get("installedFiles", {})

    row = {
        "description": ecm.get("ecmDescription", {}).get("name"),

        "software_part": ecm.get("softwarePartNumber"),

        "flash_file": installed.get("latestFileName"),

        "size_mb": round(
            (installed.get("latestFileSizeInBytes") or 0) / 1024 / 1024,
            2
        ),

        "available": installed.get("latestAvailableFlag"),

        "release_date": installed.get("latestFileReleaseDate"),

        "telematics": installed.get("isTelematicsFlashFound")
    }

    rows.append(row)

# -----------------------------------
# DATAFRAME
# -----------------------------------

df = pd.DataFrame(rows)

print("\nTABLA LIMPIA:\n")
print(df)

# -----------------------------------
# EXPORTAR CSV
# -----------------------------------

df.to_csv("Results/sis2_output.csv", index=False)

print("\nArchivo exportado: Results/sis2_output.csv")