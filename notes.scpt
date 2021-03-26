set script_path to POSIX path of ((path to me as text) & "::")

set text_file to script_path & "notes_todo.txt"

do shell script "> " & quoted form of text_file

log "Scanning notes..."

tell application "Notes"
  repeat with the_note in notes
    set note_name to name of the_note
    set note_body to body of the_note
    if note_body contains "#todo" then
        do shell script "echo  " & quoted form of note_name & " >>  " & quoted form of text_file
    end if
  end repeat
end tell

log "Done."


