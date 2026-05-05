; MT5 Trading Bot - NSIS Installer Script
; Este script genera un instalador profesional para el bot

!include "MUI2.nsh"
!include "x64.nsh"

; ============================================================================
; CONFIGURACION GENERAL
; ============================================================================
Name "MT5 Trading Bot v1.0"
OutFile "dist\MT5TradingBot_Setup_v1.0.exe"
InstallDir "$PROGRAMFILES\MT5TradingBot"
InstallDirRegKey HKCU "Software\MT5TradingBot" ""

; Architecture
!ifdef NSIS_INSTDIR_OVERRIDE
  InstallDir "$NSIS_INSTDIR_OVERRIDE"
!endif

; ============================================================================
; VARIABLES
; ============================================================================
Var StartMenuFolder

; ============================================================================
; MUI2 SETTINGS
; ============================================================================
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\modern.bmp"
!define MUI_HEADERIMAGE_RIGHT
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\modern.bmp"

!define MUI_ABORTWARNING
!define MUI_COMPONENTSPAGE_NODESC

; Language
!insertmacro MUI_LANGUAGE "Spanish"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; Start Menu Page
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\MT5TradingBot"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "Spanish"

; ============================================================================
; SECTIONS
; ============================================================================
Section "!MT5 Trading Bot (Requerido)" SecApp
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  
  ; Copiar el ejecutable principal
  File "dist\MT5TradingBot_v1.exe"
  
  ; Copiar archivos de sesión si existen
  ${If} ${FileExists} "mi_sesion.session"
    File "mi_sesion.session"
  ${EndIf}
  
  ; Crear carpetas
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\data"
  
  ; Registrar la instalación
  WriteRegStr HKCU "Software\MT5TradingBot" "" $INSTDIR
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5TradingBot" "DisplayName" "MT5 Trading Bot v1.0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5TradingBot" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5TradingBot" "DisplayIcon" "$INSTDIR\MT5TradingBot_v1.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5TradingBot" "DisplayVersion" "1.0"
  
  ; Crear desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
SectionEnd

Section "Acceso directo en escritorio" SecDesktop
  CreateShortcut "$DESKTOP\MT5 Trading Bot.lnk" "$INSTDIR\MT5TradingBot_v1.exe" "" "$INSTDIR\MT5TradingBot_v1.exe" 0
SectionEnd

Section "Acceso directo en menú inicio" SecStartMenu
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
  CreateShortcut "$SMPROGRAMS\$StartMenuFolder\MT5 Trading Bot.lnk" "$INSTDIR\MT5TradingBot_v1.exe"
  CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

; ============================================================================
; UNINSTALLER
; ============================================================================
Section "Uninstall"
  ; Eliminar accesos directos
  Delete "$DESKTOP\MT5 Trading Bot.lnk"
  
  ; Eliminar carpeta del menú inicio
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"
  
  ; Eliminar archivos
  Delete "$INSTDIR\MT5TradingBot_v1.exe"
  Delete "$INSTDIR\mi_sesion.session"
  Delete "$INSTDIR\Uninstall.exe"
  
  ; Limpiar registro
  DeleteRegKey HKCU "Software\MT5TradingBot"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5TradingBot"
  
SectionEnd

; ============================================================================
; DESCRIPTIONS
; ============================================================================
LangString DESC_SecApp ${LANG_SPANISH} "Instala el MT5 Trading Bot (requerido)"
LangString DESC_SecDesktop ${LANG_SPANISH} "Crea un acceso directo en el escritorio"
LangString DESC_SecStartMenu ${LANG_SPANISH} "Crea acceso directo en el menú inicio"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecApp} $(DESC_SecApp)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
