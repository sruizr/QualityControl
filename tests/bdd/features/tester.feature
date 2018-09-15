Feature: Tester resource is configured

  Background: Setup environment
    Given I set base URL to "http://quactrl.org"
    And I set "Authorization" header to "context.resp_auth"

  Scenario: Config a tool successfully
    When I make a PUT request to "/tester/correct_loc"
    Then the response status code should equal to 200

  Scenario: Config a tool with error
    When I make a PUT request to "/tester/incorrect_loc"
    Then the response status code should equal to 404
    And the response header "status" should equal "404 Not Found"

  Scenario: A tester shouldn't accept testing without configuration
    When I make a POST request to "/tester" with json "{'item': {'part_number': 'known_pn', 'serial_number': '123456789'}}"
    Then the response status code should equal 4??
    When I make a GET request to "/tester"
    Then the response status code should equal 4??
