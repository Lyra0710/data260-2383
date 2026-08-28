# Domain Schema

## Domain - Community sports league fixtures

## Intended User
As per my interpretation, this form is intended for a league manager to create and schedule upcoming sports fixtures. 

## Entity - Sports Fixture
<!-- Name, teams, day, time, location
Primary Field - fixtureName
Secondary Field - teams
date, time and location
submitters email 
Content description field 
dropdown - Sport type
checkbox for conditions
submit button  -->
### Fields and Descriptions
| Field | Type | Required | Description |
|---|---|---|---|
| fixtureName | String | Yes | Name of the scheduled fixture |
| teams | String | Yes | Teams participating in the fixture |
| date | Date | Yes | Date of the fixture |
| time | Time | Yes | Starting time of the fixture |
| location | String | Yes | Location where the fixture will take place |
| submitterEmail | Email | Yes | Email address of the league manager |
| description | String | Yes | Additional details about the fixture |
| sportType | String | Yes | Type of sport being played |
| termsAccepted | Boolean | Yes | Whether the manager accepted the terms and conditions |
| submissionDate | Date-time | Generated | Date and time when the form was successfully submitted |

### Category values - Dropdown for Sport Type
- Soccer
- Basketball
- Tennis
- Pickleball