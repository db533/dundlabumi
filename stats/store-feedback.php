<?php

/**
* Plugin Name: Store Feedback Form with Reviews
* Plugin URI: https://www.example.com/
* Description: Allows logged in users to provide feedback and displays a summary and individual reviews.
* Version: 1.1
* Author: Your Name
* Author URI: https://www.example.com/
**/

// Function to save the feedback
function store_feedback_save() {
    if (is_user_logged_in()) {
        $user_id = get_current_user_id();
        $user_info = get_userdata($user_id);

        // Check if the form is submitted
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            // Sanitize and store the feedback data
            $rating = intval($_POST['rating']);
            // Check if recommendation is 'jā' and set it accordingly for email
            $recommend = sanitize_text_field($_POST['recommend']) === 'jā' ? 'Jā' : 'Nē';
            $review = sanitize_textarea_field($_POST['review']);
            $review_date = current_time('mysql'); // Get current date and time

            // Update user meta with the new information
            update_user_meta($user_id, 'store_rating', $rating);
            // Save 'jā' or 'nē' instead of 'Yes' or 'No'
            update_user_meta($user_id, 'store_recommend', $recommend === 'Jā' ? 'jā' : 'nē');
            update_user_meta($user_id, 'store_review', $review);
            update_user_meta($user_id, 'store_review_date', $review_date);

            // Prepare to send the email
            $to = array('db5331@gmail.com', 'dacite.berzina@gmail.com');
            //$to = array('db5331@gmail.com');
            $subject = 'Saņemta jauna atsauksme par mūsu veikalu';
            $headers = array('Content-Type: text/html; charset=UTF-8');

            // Use get_avatar_url to get the user's avatar URL.
            $avatar_url = get_avatar_url($user_id);

            // Prepare the email content
            $message = '<h3>Jauna atsauksme:</h3>';
            $message .= '<p><strong>Lietotājs: </strong>' . esc_html($user_info->user_login) . '</p>';
            $message .= '<p><strong>Lietotāja epasta adrese: </strong>' . esc_html($user_info->user_email) . '</p>';
            $message .= '<p><img src="' . esc_url($avatar_url) . '" alt="User Avatar" /></p>';
            $message .= '<p><strong>Novērtējums: </strong>' . esc_html($rating) . '</p>';
            $message .= '<p><strong>Atsauksmes teksts: </strong>' . nl2br(esc_html($review)) . '</p>';
            $message .= '<p><strong>Vai iesaka: </strong>' . $recommend . '</p>'; // Here 'Jā' or 'Nē' will be displayed

            // Send the email
            foreach ($to as $recipient) {
                wp_mail($recipient, $subject, $message, $headers);
            }
            // Optional: Perform other actions like redirection
        }
    }
}

// Shortcode to display the feedback form
function store_feedback_form_shortcode() {
    ob_start();
    if (is_user_logged_in()) {
        $user_id = get_current_user_id();
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            store_feedback_save();
            // Redirect to the specified page after submitting the form
            wp_redirect('https://dundlabumi.lv/index.php/klientu-atsauksmes/');
            exit;
        }
        ?>
        <p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Vienmēr esam pateicīgi par ieteikumiem un atsauksmēm. Pastāstiet kas patika un ko varam uzlabot. Labprāt uzklausām!</p><br>
        <form method="post">
            <p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Novērtē mūsu veikalu: <br>(1 = slikts, 5 = labs)</p>
            <table class="ratings-table">
                <tr>
                    <?php for ($i = 1; $i <= 5; $i++): ?>
                        <td style="font-size: 24px;">
                            <label>
                                <input type="radio" name="rating" value="<?php echo $i; ?>">
                                <?php echo $i; ?>
                            </label>
                        </td>
                    <?php endfor; ?>
                </tr>
            </table>
            <p></p>
            <p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Vai Jūs ieteiktu mūsu veikalu saviem draugiem?</p>
            <div class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">
                <label><input type="radio" name="recommend" value="jā"> Jā  </label>
                <label><input type="radio" name="recommend" value="nē"> Nē</label>
            </div>
            <p></p>
            <p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Atsauksme:</p>
            <textarea name="review"></textarea>
            <div>
                <button type="submit">Pievienot atsauksmi</button>
            </div>
        </form>
        <?php
    } else {
        echo '<h3>Lai iesniegt recenziju, jāpierakstās vietnē. Spiežat "Ienāc ar Facebook" vai "Ienāc ar Google".</h3>';
        // Optional: Display a login form or link
    }
    return ob_get_clean();
}


// Function to display individual reviews
function store_feedback_reviews($score_filter = null) {
    $args = array(
        'meta_query' => array('relation' => 'AND'),
        'orderby' => 'registered', // or any other default sorting
        'order'   => 'DESC',
    );

    // Add score filter to query if set
    if ($score_filter !== null) {
        $args['meta_query'][] = array(
            'key'     => 'store_rating',
            'value'   => $score_filter,
            'compare' => '=',
        );
    } else {
        // Add a condition to ensure a review exists
        $args['meta_query'][] = array(
            'key'     => 'store_rating',
            'compare' => 'EXISTS',
        );
    }

    // Fetch users based on the modified query
    $users = get_users($args);

// Start of the table
    echo "<table class='reviews-table' style='width: 100%;'>";
    echo "<tr>
            <th style='width: 15%;'>Klients</th>
            <th style='width: 15%;'>Novērtējums</th>
            <th style='width: 60%;'>Atsauksme</th>
            <th style='width: 15%;'>Vai iesaka?</th>
          </tr>";

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $review = get_user_meta($user->ID, 'store_review', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);
        $thumbs_icon = $recommend === 'jā' ? 'https://dundlabumi.lv/wp-content/uploads/2023/11/thumbs-up.png' : 'https://dundlabumi.lv/wp-content/uploads/2023/11/thumbs-down.png'; // Replace with actual image URLs

        // Get user avatar
        $avatar = get_avatar_url($user->ID);

        // Set the desired height and width for the image
        $image_height = '30'; // height in pixels
        $image_width = '30'; // width in pixels

        // Table row for each review
        $review_date = get_user_meta($user->ID, 'store_review_date', true);
        $response = get_user_meta($user->ID, 'store_review_response', true);
        $response_date = get_user_meta($user->ID, 'store_review_response_date', true);

        // Display review with dates
        echo "<tr>";
        echo "<td style='vertical-align: top; text-align: top; padding: 4px; line-height: 1.2;'><img src='$avatar' alt='User Avatar' style='max-height: 50px; max-width: 50px;''></td>";
        echo "<td style='vertical-align: top; text-align: top; padding: 4px; line-height: 1.2; font-size: 16px;'>$rating no 5</td>";

        if ($response) {
            $formatted_response_date = (new DateTime($response_date))->format('d-m-Y');
            echo "<td style='vertical-align: top; text-align: left; padding: 4px; line-height: 1.2; font-size: 16px;'><strong>Atsauksme: </strong>$review<br><strong>Mūsu atbilde: </strong> $response<br><em>Datums: $formatted_response_date</em></td>";
        } else {
            $formatted_review_date = (new DateTime($review_date))->format('d-m-Y');
            echo "<td style='vertical-align: top; text-align: left; padding: 4px; line-height: 1.2; font-size: 16px;'>$review<br><em>Datums: $formatted_review_date</em></td>";
        }
        echo "<td style='vertical-align: top; text-align: center; padding: 4px; line-height: 1.2;'><img src='$thumbs_icon' alt='$recommend' height='$image_height' width='$image_width'></td>";
        echo "</tr>";
    }

    echo "</table>"; // End of the table}
}

// Function to calculate and display the summary of reviews
function store_feedback_summary() {
    $users = get_users();
    $total_rating = $total_recommend = $count = 0;

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);

        if ($rating) {
            $total_rating += $rating;
            $total_recommend += ($recommend === 'jā' ? 1 : 0);
            $count++;
        }
    }

    echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Zemāk varat redzēt sarakstu ar saņemtajām atsauksmēm. <a href="https://dundlabumi.lv/index.php/atsauksmes/" title="Atsauksmes">Šeit varat pievienot savu atsauksmi</a>. </p><br>';

    if ($count > 0) {
        $average_rating = round($total_rating / $count, 1);
        $average_rating_percentage = ($average_rating / 5) * 100; // Convert to percentage

        echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Vidējais veikala vērtējums: <strong>' . $average_rating . '</strong> no 5.</p><br>';
        $recommend_percentage = round(($total_recommend / $count) * 100);
        if ($recommend_percentage > 67) {
            echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Cik % no recenzijām ieteiktu mūsu veikalu saviem draugiem: <strong>' . $recommend_percentage . '%</strong></p><br>';
        }
    } else {
        // Handle case where there are no ratings
        echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Vidējais veikala vērtējums: Gaidām pirmo atsauksmi :)</p><br>';
        echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Cik % no recenzijām ieteiktu mūsu veikalu saviem draugiem: Gaidām pirmo atsauksmi :)</p><br>';
    }
    echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Pievienot atsauksmes ir iespējams tikai kopš 27.11.2023. Tāpēc te pagaidām ir tik maz to atsauksmju, bet Jūs varat būt viens no pirmajiem!</p><br>';
    echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Atlasīt atsauksmes pēc novērtējuma: ';
    echo '<a href="?score=1" title="">1</a>  ';
    echo '<a href="?score=2" title="">2</a>  ';
    echo '<a href="?score=3" title="">3</a>  ';
    echo '<a href="?score=4" title="">4</a>  ';
    echo '<a href="?score=5" title="">5</a></p><br>';
}

// Shortcode to display the summary and reviews
function store_feedback_display_shortcode($atts) {
    ob_start();

    // Check for score parameter in URL
    $score_filter = isset($_GET['score']) ? intval($_GET['score']) : null;

    store_feedback_summary();
    store_feedback_reviews($score_filter); // Pass the score filter to the function
    echo '<p class="has-medium-font-size" style="line-height: 1; margin-top: 0; margin-bottom: 0;">Un šādas atsauksmes esam saņēmuši, sarakstoties ar klientiem:</p><br>';

    return ob_get_clean();
}

function store_feedback_response_page() {
    echo '<h1>Respond to Reviews</h1>';

    $users = get_users(array(
        'meta_key'     => 'store_review',
        'meta_value'   => '',
        'meta_compare' => '!='
    ));

    echo '<form action="" method="post">';

    echo "<table>";
    echo "<tr>
            <th style='width: 10%;'>Select</th>
            <th style='width: 10%;'>Reviewer</th>
            <th style='width: 10%;'>Score</th>
            <th style='width: 40%;'>Review</th>
            <th style='width: 10%;'>Recommend?</th>
            <th style='width: 30%;'>Response</th>
          </tr>";

    foreach ($users as $user) {
        $review = get_user_meta($user->ID, 'store_review', true);
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true) === 'jā' ? 'Yes' : 'No';
        $response = get_user_meta($user->ID, 'store_review_response', true);
        $avatar = get_avatar_url($user->ID);

        echo "<tr style='text-align: center;'>";
        echo "<td><input type='checkbox' name='review_user_ids[]' value='{$user->ID}'></td>";
        echo "<td><img src='$avatar' alt='User Avatar' style='height: 50px; width: 50px;'></td>";
        echo "<td>{$rating} / 5</td>";
        echo "<td>{$review}</td>";
        echo "<td>{$recommend}</td>";
        echo "<td>{$response}</td>";
        echo "</tr>";
    }

    echo "</table>";

    echo '<textarea name="response" style="width: 100%; min-height: 100px;"></textarea>';
    echo '<input type="submit" value="Submit Response" style="margin-top: 10px;">';
    echo '</form>';
}

function store_feedback_save_response() {
    if (isset($_POST['review_user_ids']) && isset($_POST['response'])) {
        $response = sanitize_textarea_field($_POST['response']);
        $response_date = current_time('mysql');

        foreach ($_POST['review_user_ids'] as $user_id) {
            update_user_meta($user_id, 'store_review_response', $response);
            update_user_meta($user_id, 'store_review_response_date', $response_date);
        }
    }
}
add_action('admin_init', 'store_feedback_save_response');


function store_feedback_admin_menu() {
    add_menu_page(
        'Respond to reviews',
        'Respond to reviews',
        'manage_options',
        'store-feedback-responses',
        'store_feedback_response_page',
        'dashicons-admin-comments',
        20
    );
}
add_action('admin_menu', 'store_feedback_admin_menu');

add_shortcode('store_feedback_form', 'store_feedback_form_shortcode');
add_shortcode('store_feedback_display', 'store_feedback_display_shortcode');

// Register AJAX actions if needed
add_action('wp_ajax_store_feedback_save', 'store_feedback_save');
add_action('wp_ajax_nopriv_store_feedback_save', 'store_feedback_save');
?>
