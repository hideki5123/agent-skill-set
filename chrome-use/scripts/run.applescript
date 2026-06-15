-- chrome-use run driver (TEMPLATE)
-- __APP__ is substituted with the literal target app name by chrome-use.sh before
-- running. The app name MUST be literal: `tell application someVariable` cannot load
-- the app's AppleScript terminology (execute javascript / active tab / URL / tabs),
-- which fails to compile. All Chromium browsers share Chrome's dictionary, so any
-- of them works once substituted in literally.
--
-- argv: url, jsFile, waitSelector, maxWaitSecs, keepTab(0|1)
on run argv
	set theURL to item 1 of argv
	set jsFile to item 2 of argv
	set waitSel to item 3 of argv
	set maxWait to (item 4 of argv) as integer
	set keepTab to item 5 of argv

	set jsCode to read (POSIX file jsFile) as «class utf8»

	set didOpen to false
	set foundWin to 0
	set foundTab to 0

	tell application "__APP__"
		activate
		if theURL is not "" then
			set winCount to (count of windows)
			repeat with wi from 1 to winCount
				set tabCount to (count of tabs of window wi)
				repeat with ti from 1 to tabCount
					if (URL of tab ti of window wi) contains theURL then
						set foundWin to wi
						set foundTab to ti
						exit repeat
					end if
				end repeat
				if foundWin > 0 then exit repeat
			end repeat
			if foundWin = 0 then
				-- Opening requires a full URL with scheme; the search term may be a
				-- bare substring, so normalize only when we actually open.
				set openURL to theURL
				if (openURL does not start with "http://") and (openURL does not start with "https://") then
					set openURL to "https://" & openURL
				end if
				if (count of windows) = 0 then make new window
				tell window 1 to make new tab with properties {URL:openURL}
				set foundWin to 1
				set foundTab to (count of tabs of window 1)
				set didOpen to true
			end if
			set active tab index of window foundWin to foundTab
			set index of window foundWin to 1
		end if

		-- Wait for the page to be ready (and, if requested, for a selector).
		set isReady to false
		repeat maxWait times
			delay 1
			try
				set rs to ""
				tell active tab of front window to set rs to execute javascript "document.readyState"
				if rs is "complete" or rs is "interactive" then
					if waitSel is "" then
						set isReady to true
						exit repeat
					else
						set present to "false"
						tell active tab of front window to set present to (execute javascript "(!!document.querySelector('" & waitSel & "')).toString()")
						if present is "true" then
							set isReady to true
							exit repeat
						end if
					end if
				end if
			end try
		end repeat

		if (waitSel is not "") and (isReady is false) then
			error "wait-timeout: selector not found within " & maxWait & "s: " & waitSel
		end if

		-- Run the main JS. Errors propagate to the caller (bash maps them).
		set theResult to ""
		tell active tab of front window to set theResult to execute javascript jsCode

		-- Clean up only the tab we opened ourselves.
		if didOpen and keepTab is "0" then
			try
				close tab foundTab of window foundWin
			end try
		end if

		return theResult
	end tell
end run
