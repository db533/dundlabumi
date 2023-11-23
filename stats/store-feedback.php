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

        // Check if the form is submitted
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            // Sanitize and store the feedback data
            $rating = intval($_POST['rating']);
            $recommend = sanitize_text_field($_POST['recommend']);
            $review = sanitize_textarea_field($_POST['review']);

            update_user_meta($user_id, 'store_rating', $rating);
            update_user_meta($user_id, 'store_recommend', $recommend);
            update_user_meta($user_id, 'store_review', $review);

            // Optional: Send an email notification or perform other actions
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
            echo '<meta http-equiv="refresh" content="0">';
        }
        ?>
        <form method="post">
            <h4>Novērtē mūsu veikalu</h4>
            <div>
                <!-- Star rating input -->
                <?php for ($i = 1; $i <= 5; $i++): ?>
                    <input type="radio" name="rating" value="<?php echo $i; ?>"> <?php echo $i; ?>
                <?php endfor; ?>
            </div>
            <h4>Vai Jūs ieteiktu mūsu veikalu saviem draugiem?</h4>
            <div>
                <label><input type="radio" name="recommend" value="jā"> Yes</label>
                <label><input type="radio" name="recommend" value="nē"> No</label>
            </div>
            <h3>Atsauksme</h3>
            <textarea name="review"></textarea>
            <div>
                <button type="submit">Pievienot atsauksmi</button>
            </div>
        </form>
        <?php
    } else {
        echo '<p>Lai iesniegt recenziju, jāpieslēdzas vietnei.</p>';
        // Optional: Display a login form or link
    }
    return ob_get_clean();
}

// Function to display individual reviews
function store_feedback_reviews($sort = 'rating') {
    $args = array(
        'meta_query' => array(
            'relation' => 'AND',
            array(
                'key'     => 'store_rating',
                'compare' => 'EXISTS',
            ),
            array(
                'key'     => 'store_review',
                'compare' => 'EXISTS',
            ),
        ),
        'orderby' => $sort === 'rating' ? 'meta_value_num' : 'registered',
        'order'   => 'DESC',
        'meta_key' => 'store_rating',
    );
    $users = get_users($args);

// Start of the table
    echo "<table class='reviews-table'>";
    echo "<tr><th>User</th><th>Rating</th><th>Review</th><th>Recommend</th></tr>";

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $review = get_user_meta($user->ID, 'store_review', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);
        $thumbs_icon = $recommend === 'yes' ? 'https://dundlabumi.lv/wp-content/uploads/2023/11/thumbs-up.png' : 'https://dundlabumi.lv/wp-content/uploads/2023/11/thumbs-down.png'; // Replace with actual image URLs

        // Get user avatar
        $avatar = get_avatar_url($user->ID);

        // Set the desired height and width for the image
        $image_height = '30'; // height in pixels
        $image_width = '30'; // width in pixels

        // Table row for each review
        echo "<tr>";
        echo "<td><img src='$avatar' alt='User Avatar' height='50' width='50'></td>"; // Displaying the user's avatar
        echo "<td>$rating / 5</td>";
        echo "<td>$review</td>";
        echo "<td><img src='$thumbs_icon' alt='$recommend' height='$image_height' width='$image_width'></td>";
        echo "</tr>";
    }

    echo "</table>"; // End of the table}

// Function to calculate and display the summary of reviews
function store_feedback_summary() {
    $users = get_users();
    $total_rating = $total_recommend = $count = 0;

    foreach ($users as $user) {
        $rating = get_user_meta($user->ID, 'store_rating', true);
        $recommend = get_user_meta($user->ID, 'store_recommend', true);

        if ($rating) {
            $total_rating += $rating;
            $total_recommend += ($recommend === 'yes' ? 1 : 0);
            $count++;
        }
    }

    $average_rating = $count > 0 ? round($total_rating / $count, 1) : 0;
    $recommend_percentage = $count > 0 ? round(($total_recommend / $count) * 100) : 0;

    echo "<p>Vidējais veikala vērtējums: $average_rating no 5</p>";
    echo "<p>Cik % no recenzijām ieteiktu mūsu veikalu saviem draugiem: $recommend_percentage%</p>";
}

// Shortcode to display the summary and reviews
function store_feedback_display_shortcode($atts) {
    ob_start();

    $atts = shortcode_atts( array(
        'sort' => 'rating',
    ), $atts );

    store_feedback_summary();
    store_feedback_reviews($atts['sort']);

    return ob_get_clean();
}

add_shortcode('store_feedback_form', 'store_feedback_form_shortcode');
add_shortcode('store_feedback_display', 'store_feedback_display_shortcode');

// Register AJAX actions if needed
add_action('wp_ajax_store_feedback_save', 'store_feedback_save');
add_action('wp_ajax_nopriv_store_feedback_save', 'store_feedback_save');

?>
