Feature: Tester resource without cavities tests one item
  Background: Setup environment
    Given I set base URL to "http://quactrl.org"
    And I set "Authorization" header to "context.resp_auth"
    When I make a PUT request to "/tester/simple_runner_loc"

  Scenario: An item is sent for testing
    When I make a POST request to "/tester" with json "{'item': {'part_number': 'known_pn', 'serial_number': '123456789'}}"
    Then the response status code should equal 101
    And the response structure should equal to "TestData"
    And the response header "status" should equal "101 PROCESSING"
    When I make a GET request to "/tester"
    Then the response structure should equal to "StatusData"
    And the response status code should equal to 206
    When I make a GET request to "/tester"
    Then the response status code should equal 200
    And the response structure should equal to "StatusData"
    And the response json should contain

  Scenario: An unknow item is sent for testing
    When I make a POST request to "/tester" with json "{'item': {'part_number': 'unknown_pn', 'serial_number': '123456789'}}"
    Then the response status code should equal 404
    And the responsel header "status" should equal "404 Not Found"
    When I make a GET request to "/tester"
    Then the response status code should equal 200
    And the responsel json

  Scenario: An testing cycle is cancelled
    When I make a POST request to "/tester" with json "{'item': {'part_number': 'known_pn', 'serial_number': '123456789'}}"
    And I make a DEL request to "/tester/cancel "
    Then the response status code should equal 101
    And I make a GET request to "/tester"
    Then the response status code should equal 200
    And the response json "status" should equal "cancelled"


 Scenario: A cycle is finished with error
    When I make a POST request to "/tester" with json "{'item': {'part_number': 'known_pn', 'serial_number': '123_error'}}"
    Then the response status code should equal 101
    When I make a GET request to "/tester"
    Then the response status code should equal
    And I make a DEL request to "/tester/stop"
    Then the response status code should equal 101
    And I make a GET request to "/tester"
    Then the response status code should equal 200
    And the response json should contain "status.cancelled"
