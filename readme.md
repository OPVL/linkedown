# LinkedIn Learning Downloader

## Troubleshooting

### Errors

#### Error 001

A video element could not be found on the page.
This means when selenium was searching for the video pane by ID it returned no results.

This could be caused by:

* The ID of the video pane changing (view source on linkedin learning page)
* The URL supplied was not to a valid course page. Should be first video of course
* You've been redirected away from the course. Check auth credentials
