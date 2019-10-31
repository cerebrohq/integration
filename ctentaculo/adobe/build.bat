@ECHO off

if exist "ctentaculo.zxp" (
    echo "Remove exists .zxp"
	del "ctentaculo.zxp"
)

echo "Build extension"
"ZXPSignCmd.exe" -sign "plugin_template" "ctentaculo.zxp" "tentaculo_certificate.p12" "qqq"
echo "Verify extension"
"ZXPSignCmd.exe" -verify "ctentaculo.zxp"
pause